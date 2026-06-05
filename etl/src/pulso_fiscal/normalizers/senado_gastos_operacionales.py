"""Normalize Senado operational expenses for rankings.

The scraper output is kept as a traceable source table. This module builds
derived tables with explicit quality flags so the product can rank only rows
that are safe to aggregate.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from pulso_fiscal.manifest import (
    PipelineManifest,
    ProcessedFileRecord,
    make_run_id,
    sha256_file,
)

ETL_DIR = Path(__file__).resolve().parents[3]
DEFAULT_PROCESSED_DIR = ETL_DIR / "data" / "processed"

EXPENSE_FILE_PREFIX = "senado_gastos_operacionales_"
PARLIAMENTARIAN_FILE_PREFIX = "senado_gastos_operacionales_parlamentarios_"

STATUS_OK = "ok"
STATUS_AJUSTE = "ajuste"
STATUS_DUPLICADO = "duplicado"
STATUS_MONTO_EN_TEXTO = "monto_en_texto"
STATUS_NOTA = "nota"
STATUS_SIN_CATEGORIA = "sin_categoria"
STATUS_SIN_MONTO = "sin_monto"
DEFAULT_PUBLICATION_FROM = "2021-01"

MONEY_TEXT_RE = re.compile(r"^-?\s*\$\s*[\d.\s-]+$")

CLEAN_COLUMNS = [
    "source_id",
    "row_number",
    "row_status",
    "include_in_ranking",
    "exclusion_reason",
    "fuente",
    "dataset",
    "ano",
    "mes",
    "periodo",
    "parlamentario_id",
    "parlamentario_nombre",
    "parlamentario_id_source",
    "unidad_ejecutora",
    "nombre_completo_raw",
    "categoria_id",
    "categoria_nombre",
    "categoria_key",
    "categoria_raw",
    "monto",
    "monto_raw",
    "source_url",
    "raw_file",
    "raw_body_sha256",
    "fecha_captura_utc",
]

RANKING_COLUMNS = [
    "periodo",
    "ano",
    "mes",
    "categoria_id",
    "categoria_nombre",
    "parlamentario_id",
    "parlamentario_nombre",
    "rank",
    "total_monto",
    "registros",
    "total_ajustes",
    "registros_ajuste",
    "registros_sin_monto",
    "registros_excluidos",
]

CATEGORY_COLUMNS = [
    "categoria_id",
    "categoria_nombre",
    "categoria_key",
    "rows",
    "included_rows",
    "excluded_rows",
    "total_monto",
    "raw_variant_count",
    "raw_variants",
]

CATEGORY_ALIASES = {
    "ACTIVIDADES REGIONALES": ("actividades_regionales", "Actividades regionales"),
    "ARRIENDO DE OFICINAS": ("arriendo_oficinas", "Arriendo de oficinas"),
    "ARRIENDO OFICINAS": ("arriendo_oficinas", "Arriendo de oficinas"),
    "COMPRA Y MANTENCION DOMINIO NIC": (
        "compra_mantencion_dominio_nic",
        "Compra y mantencion dominio NIC",
    ),
    "COMPRA Y MANTENCION DE DOMINIO NIC": (
        "compra_mantencion_dominio_nic",
        "Compra y mantencion dominio NIC",
    ),
    "DESC. POR PERSONAL DE APOYO": (
        "descuento_personal_apoyo",
        "Descuento por personal de apoyo",
    ),
    "DESC.PERSONAL DE APOYO": (
        "descuento_personal_apoyo",
        "Descuento por personal de apoyo",
    ),
    "DESC.POR PERSONAL APOYO": (
        "descuento_personal_apoyo",
        "Descuento por personal de apoyo",
    ),
    "DESC.POR PERSONAL DE APOYO": (
        "descuento_personal_apoyo",
        "Descuento por personal de apoyo",
    ),
    "DIFUSION": ("difusion", "Difusion"),
    "DISENO Y DESARROLLO PAG.WEB": (
        "diseno_desarrollo_pagina_web",
        "Diseno y desarrollo pagina web",
    ),
    "DISENO Y DESARROLLO PAGINA WEB": (
        "diseno_desarrollo_pagina_web",
        "Diseno y desarrollo pagina web",
    ),
    "MATERIALES DE OFICINA": ("materiales_oficina", "Materiales de oficina"),
    "OFICINAS PARLAMENTARIAS": ("oficinas_parlamentarias", "Oficinas parlamentarias"),
    "SERVICIO DE NUBE O CLOUD": ("servicio_nube_cloud", "Servicio de nube o cloud"),
    "SERVICIO NUBE O CLOUD": ("servicio_nube_cloud", "Servicio de nube o cloud"),
    "SERVICIOS MENORES": ("servicios_menores", "Servicios menores"),
    "TELEFONIA CELULAR": ("telefonia_celular", "Telefonia celular"),
    "TELEFONIA FIJA": ("telefonia_fija", "Telefonia fija"),
    "TRASLACION": ("traslacion", "Traslacion"),
}


CsvRow = dict[str, str]


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    key: str


@dataclass
class Aggregate:
    total_monto: int = 0
    registros: int = 0
    total_ajustes: int = 0
    registros_ajuste: int = 0
    registros_sin_monto: int = 0
    registros_excluidos: int = 0


@dataclass
class CategoryStats:
    name: str
    key: str
    rows: int = 0
    included_rows: int = 0
    excluded_rows: int = 0
    total_monto: int = 0
    variants: Counter[str] | None = None

    def __post_init__(self) -> None:
        if self.variants is None:
            self.variants = Counter()


@dataclass(frozen=True)
class NormalizationResult:
    clean_rows: list[CsvRow]
    ranking_rows: list[CsvRow]
    category_rows: list[CsvRow]
    quality_report: dict[str, object]


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv(ETL_DIR / ".env.local")
    args = parse_args(argv)
    run_id = args.run_id or make_run_id()

    expense_csv = args.expenses_csv or latest_csv(args.processed_dir, EXPENSE_FILE_PREFIX)
    parliamentarians_csv = args.parliamentarians_csv or optional_latest_csv(
        args.processed_dir,
        PARLIAMENTARIAN_FILE_PREFIX,
    )
    output_dir: Path = args.output_dir or args.processed_dir
    suffix = args.suffix or suffix_from_expense_path(expense_csv)

    expense_rows = read_csv(expense_csv)
    parliamentarian_rows = read_csv(parliamentarians_csv) if parliamentarians_csv else []
    result = normalize_expenses(expense_rows, parliamentarian_rows, source_path=expense_csv)

    output_dir.mkdir(parents=True, exist_ok=True)
    clean_path = output_dir / f"senado_gastos_operacionales_clean_{suffix}.csv"
    ranking_path = output_dir / f"senado_gastos_operacionales_ranking_mensual_{suffix}.csv"
    categories_path = output_dir / f"senado_gastos_operacionales_categorias_{suffix}.csv"
    quality_path = output_dir / f"senado_gastos_operacionales_quality_{suffix}.json"

    write_csv(clean_path, result.clean_rows, CLEAN_COLUMNS)
    write_csv(ranking_path, result.ranking_rows, RANKING_COLUMNS)
    write_csv(categories_path, result.category_rows, CATEGORY_COLUMNS)
    quality_path.write_text(
        json.dumps(result.quality_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Clean: {clean_path}")
    print(f"Ranking mensual: {ranking_path}")
    print(f"Categorias: {categories_path}")
    print(f"Calidad: {quality_path}")

    # Manifest
    download_manifest_path = (
        output_dir / "senado" / "gastos_operacionales" / "download_manifest.json"
    )
    output_files = [
        _processed_record("clean", clean_path, len(result.clean_rows)),
        _processed_record("ranking_mensual", ranking_path, len(result.ranking_rows)),
        _processed_record("categorias", categories_path, len(result.category_rows)),
        _processed_record("quality", quality_path, 0),
    ]
    manifest = PipelineManifest(
        dataset="senado_gastos_operacionales",
        source="Senado de Chile",
        run_id=run_id,
        generated_at_utc=datetime.now(UTC).replace(microsecond=0).isoformat(),
        period_from=suffix.split("_")[0] if "_" in suffix else suffix,
        period_to=suffix.split("_")[1] if "_" in suffix else suffix,
        download_manifest_path=str(download_manifest_path),
        input_files=[str(expense_csv), str(parliamentarians_csv) if parliamentarians_csv else ""],
        output_files=output_files,
        quality_summary=result.quality_report,
    )
    pipeline_manifest_path = (
        output_dir / "senado" / "gastos_operacionales" / "pipeline_manifest.json"
    )
    manifest.write(pipeline_manifest_path)
    print(f"Pipeline manifest: {pipeline_manifest_path}")

    if args.enforce_quality_gate or args.upload_r2 or args.load_db:
        enforce_quality_gate(result.quality_report, publication_from=args.publication_from)

    if args.upload_r2:
        _upload_processed_to_r2(manifest, run_id, output_dir)

    if args.load_db:
        from pulso_fiscal.loaders.supabase import load_pipeline  # noqa: PLC0415
        load_pipeline(manifest, clean_path, ranking_path)

    return 0


def _processed_record(name: str, path: Path, row_count: int) -> ProcessedFileRecord:
    return ProcessedFileRecord(
        name=name,
        local_path=str(path),
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        row_count=row_count,
    )


def _upload_processed_to_r2(
    manifest: PipelineManifest,
    run_id: str,
    output_dir: Path,
) -> None:
    from pulso_fiscal.storage.r2 import R2Client  # noqa: PLC0415

    r2 = R2Client()
    public_bucket = os.environ.get("R2_PUBLIC_BUCKET", "pulso-fiscal-public")
    r2_prefix = f"senado/gastos_operacionales/runs/{run_id}/processed"

    for record in manifest.output_files:
        local_path = Path(record.local_path)
        r2_key = f"{r2_prefix}/{local_path.name}"
        if not r2.object_exists(public_bucket, r2_key):
            r2.upload_file(local_path, public_bucket, r2_key)
            print(f"  Subido: {r2_key}")
        else:
            print(f"  Ya existe: {r2_key}")
        record.r2_key = r2_key
        record.r2_bucket = public_bucket
        record.public_url = r2.build_public_url(r2_key)

    # Subir a latest/
    for record in manifest.output_files:
        local_path = Path(record.local_path)
        latest_key = f"senado/gastos_operacionales/latest/{local_path.name}"
        r2.upload_file(local_path, public_bucket, latest_key)
        print(f"  Latest actualizado: {latest_key}")

    # Subir manifest
    manifest_r2_key = f"senado/gastos_operacionales/runs/{run_id}/pipeline_manifest.json"
    manifest.r2_manifest_key = manifest_r2_key
    manifest.public_manifest_url = r2.build_public_url(manifest_r2_key)
    manifest_bytes = (
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    r2.upload_bytes(manifest_bytes, public_bucket, manifest_r2_key, "application/json")
    r2.upload_bytes(
        manifest_bytes,
        public_bucket,
        "senado/gastos_operacionales/latest/pipeline_manifest.json",
        "application/json",
    )
    print(f"  Manifest subido: {manifest_r2_key}")


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normaliza gastos operacionales del Senado para rankings."
    )
    parser.add_argument("--expenses-csv", type=Path, default=None)
    parser.add_argument("--parliamentarians-csv", type=Path, default=None)
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED_DIR)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--suffix", default=None)
    parser.add_argument(
        "--run-id",
        default=None,
        help="Identificador unico de la corrida. Si no se pasa, se genera automaticamente.",
    )
    parser.add_argument(
        "--upload-r2",
        action="store_true",
        default=False,
        help="Sube archivos procesados a Cloudflare R2 al finalizar.",
    )
    parser.add_argument(
        "--load-db",
        action="store_true",
        default=False,
        help="Carga datos limpios a Supabase/Postgres al finalizar.",
    )
    parser.add_argument(
        "--publication-from",
        type=period_label,
        default=DEFAULT_PUBLICATION_FROM,
        help="Primer periodo publico usado para gates de calidad. Por defecto: 2021-01.",
    )
    parser.add_argument(
        "--enforce-quality-gate",
        action="store_true",
        default=False,
        help="Ejecuta el gate de calidad aunque no se suba a R2 ni se cargue DB.",
    )
    return parser.parse_args(argv)


def normalize_expenses(
    expense_rows: Sequence[CsvRow],
    parliamentarian_rows: Sequence[CsvRow] | None = None,
    *,
    source_path: Path | None = None,
) -> NormalizationResult:
    parliamentarian_rows = parliamentarian_rows or []
    name_catalog = build_name_catalog([*expense_rows, *parliamentarian_rows])
    source_seen: dict[str, tuple[str, ...]] = {}
    duplicate_source_ids: Counter[str] = Counter()
    conflicting_duplicate_source_ids: set[str] = set()

    clean_rows: list[CsvRow] = []
    aggregates: dict[tuple[str, str, str], Aggregate] = defaultdict(Aggregate)
    aggregate_names: dict[tuple[str, str, str], tuple[str, str, str, str, str]] = {}
    category_stats: dict[str, CategoryStats] = {}
    row_status_counts: Counter[str] = Counter()
    missing_unit_count = 0
    amount_values: list[int] = []
    problem_examples: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row_number, row in enumerate(expense_rows, start=1):
        source_id = clean_cell(row.get("source_id"))
        source_signature = identity_signature(row)
        is_duplicate = False
        if source_id:
            previous_signature = source_seen.get(source_id)
            if previous_signature is None:
                source_seen[source_id] = source_signature
            else:
                is_duplicate = True
                duplicate_source_ids[source_id] += 1
                if previous_signature != source_signature:
                    conflicting_duplicate_source_ids.add(source_id)

        amount = parse_amount(row.get("monto"))
        if amount is not None:
            amount_values.append(amount)

        category = normalize_category(row.get("gastos_operacionales", ""))
        parliamentarian_id, parliamentarian_id_source = parliamentarian_identity(row)
        if parliamentarian_id_source == "nombre_completo":
            missing_unit_count += 1
        parliamentarian_name = name_catalog.get(
            parliamentarian_id,
            display_person_name(row.get("nombre_completo", "")),
        )

        row_status = classify_row(row, category, amount, is_duplicate)
        include_in_ranking = row_status == STATUS_OK
        exclusion_reason = "" if include_in_ranking else row_status
        row_status_counts[row_status] += 1

        clean_row = {
            "source_id": source_id,
            "row_number": str(row_number),
            "row_status": row_status,
            "include_in_ranking": "true" if include_in_ranking else "false",
            "exclusion_reason": exclusion_reason,
            "fuente": clean_cell(row.get("fuente")),
            "dataset": clean_cell(row.get("dataset")),
            "ano": clean_cell(row.get("ano")),
            "mes": clean_cell(row.get("mes")),
            "periodo": clean_cell(row.get("periodo")),
            "parlamentario_id": parliamentarian_id,
            "parlamentario_nombre": parliamentarian_name,
            "parlamentario_id_source": parliamentarian_id_source,
            "unidad_ejecutora": clean_cell(row.get("unidad_ejecutora")),
            "nombre_completo_raw": clean_cell(row.get("nombre_completo")),
            "categoria_id": category.id,
            "categoria_nombre": category.name,
            "categoria_key": category.key,
            "categoria_raw": clean_cell(row.get("gastos_operacionales")),
            "monto": "" if amount is None else str(amount),
            "monto_raw": clean_cell(row.get("monto")),
            "source_url": clean_cell(row.get("source_url")),
            "raw_file": clean_cell(row.get("raw_file")),
            "raw_body_sha256": clean_cell(row.get("raw_body_sha256")),
            "fecha_captura_utc": clean_cell(row.get("fecha_captura_utc")),
        }
        clean_rows.append(clean_row)
        collect_problem_example(problem_examples, row_status, clean_row)

        update_category_stats(category_stats, category, clean_row, amount, include_in_ranking)
        update_aggregate(aggregates, aggregate_names, clean_row, amount, row_status)

    category_names = {
        category_id: stats.name for category_id, stats in category_stats.items()
    }
    ranking_rows = build_ranking_rows(aggregates, aggregate_names, category_names)
    category_rows = build_category_rows(category_stats)
    quality_report = build_quality_report(
        source_path=source_path,
        source_rows=expense_rows,
        clean_rows=clean_rows,
        ranking_rows=ranking_rows,
        category_rows=category_rows,
        row_status_counts=row_status_counts,
        duplicate_source_ids=duplicate_source_ids,
        conflicting_duplicate_source_ids=conflicting_duplicate_source_ids,
        missing_unit_count=missing_unit_count,
        amount_values=amount_values,
        problem_examples=problem_examples,
    )

    return NormalizationResult(
        clean_rows=clean_rows,
        ranking_rows=ranking_rows,
        category_rows=category_rows,
        quality_report=quality_report,
    )


def classify_row(
    row: Mapping[str, str],
    category: Category,
    amount: int | None,
    duplicate: bool,
) -> str:
    if duplicate:
        return STATUS_DUPLICADO
    raw_category = clean_cell(row.get("gastos_operacionales"))
    category_key_value = category.key
    if not raw_category:
        return STATUS_SIN_CATEGORIA
    if category_key_value.startswith("NOTA"):
        return STATUS_NOTA
    if amount is None and MONEY_TEXT_RE.fullmatch(raw_category.strip()):
        return STATUS_MONTO_EN_TEXTO
    if amount is None:
        return STATUS_SIN_MONTO
    if amount < 0:
        return STATUS_AJUSTE
    return STATUS_OK


def update_aggregate(
    aggregates: dict[tuple[str, str, str], Aggregate],
    aggregate_names: dict[tuple[str, str, str], tuple[str, str, str, str, str]],
    clean_row: CsvRow,
    amount: int | None,
    row_status: str,
) -> None:
    key = (
        clean_row["periodo"],
        clean_row["categoria_id"],
        clean_row["parlamentario_id"],
    )
    aggregate = aggregates[key]
    aggregate_names[key] = (
        clean_row["ano"],
        clean_row["mes"],
        clean_row["categoria_nombre"],
        clean_row["parlamentario_nombre"],
        clean_row["parlamentario_id"],
    )

    if row_status == STATUS_OK and amount is not None:
        aggregate.total_monto += amount
        aggregate.registros += 1
        return
    if row_status == STATUS_AJUSTE and amount is not None:
        aggregate.total_ajustes += amount
        aggregate.registros_ajuste += 1
    if row_status in {STATUS_SIN_MONTO, STATUS_MONTO_EN_TEXTO}:
        aggregate.registros_sin_monto += 1
    aggregate.registros_excluidos += 1


def build_ranking_rows(
    aggregates: Mapping[tuple[str, str, str], Aggregate],
    aggregate_names: Mapping[tuple[str, str, str], tuple[str, str, str, str, str]],
    category_names: Mapping[str, str],
) -> list[CsvRow]:
    rows_by_period_category: dict[tuple[str, str], list[tuple[tuple[str, str, str], Aggregate]]] = (
        defaultdict(list)
    )
    for key, aggregate in aggregates.items():
        if aggregate.registros == 0:
            continue
        rows_by_period_category[(key[0], key[1])].append((key, aggregate))

    ranking_rows: list[CsvRow] = []
    for period_category in sorted(rows_by_period_category):
        ranked = sorted(
            rows_by_period_category[period_category],
            key=lambda item: (
                -item[1].total_monto,
                aggregate_names[item[0]][3],
                item[0][2],
            ),
        )
        for rank, (key, aggregate) in enumerate(ranked, start=1):
            year, month, fallback_category_name, parliamentarian_name, parliamentarian_id = (
                aggregate_names[key]
            )
            category_name = category_names.get(key[1], fallback_category_name)
            ranking_rows.append(
                {
                    "periodo": key[0],
                    "ano": year,
                    "mes": month,
                    "categoria_id": key[1],
                    "categoria_nombre": category_name,
                    "parlamentario_id": parliamentarian_id,
                    "parlamentario_nombre": parliamentarian_name,
                    "rank": str(rank),
                    "total_monto": str(aggregate.total_monto),
                    "registros": str(aggregate.registros),
                    "total_ajustes": str(aggregate.total_ajustes),
                    "registros_ajuste": str(aggregate.registros_ajuste),
                    "registros_sin_monto": str(aggregate.registros_sin_monto),
                    "registros_excluidos": str(aggregate.registros_excluidos),
                }
            )
    return ranking_rows


def update_category_stats(
    stats: dict[str, CategoryStats],
    category: Category,
    clean_row: CsvRow,
    amount: int | None,
    include_in_ranking: bool,
) -> None:
    category_stats = stats.setdefault(
        category.id,
        CategoryStats(name=category.name, key=category.key),
    )
    category_stats.rows += 1
    if category_stats.variants is not None:
        category_stats.variants[clean_row["categoria_raw"]] += 1
    if include_in_ranking:
        category_stats.included_rows += 1
        if amount is not None:
            category_stats.total_monto += amount
    else:
        category_stats.excluded_rows += 1


def build_category_rows(stats: Mapping[str, CategoryStats]) -> list[CsvRow]:
    rows: list[CsvRow] = []
    for category_id, category_stats in sorted(stats.items()):
        variants = category_stats.variants
        raw_variants = ""
        raw_variant_count = 0
        if variants is not None:
            raw_variant_count = len(variants)
            raw_variants = " | ".join(
                f"{name} ({count})" for name, count in variants.most_common()
            )
        rows.append(
            {
                "categoria_id": category_id,
                "categoria_nombre": category_stats.name,
                "categoria_key": category_stats.key,
                "rows": str(category_stats.rows),
                "included_rows": str(category_stats.included_rows),
                "excluded_rows": str(category_stats.excluded_rows),
                "total_monto": str(category_stats.total_monto),
                "raw_variant_count": str(raw_variant_count),
                "raw_variants": raw_variants,
            }
        )
    return rows


def normalize_category(raw_value: str) -> Category:
    key = category_key(raw_value)
    if not key:
        return Category(id="sin_categoria", name="Sin categoria", key="")
    alias = CATEGORY_ALIASES.get(key)
    if alias:
        return Category(id=alias[0], name=alias[1], key=key)
    return Category(id=slugify(key), name=display_category_name(key), key=key)


def category_key(raw_value: str) -> str:
    value = normalize_ascii(raw_value).upper()
    value = value.replace("PAG.WEB", "PAGINA WEB")
    value = value.replace("PAG. WEB", "PAGINA WEB")
    value = value.replace("PAGINA WEB.", "PAGINA WEB")
    value = re.sub(r"\s+", " ", value).strip()
    if value.endswith(" SENADORES"):
        value = value[: -len(" SENADORES")].strip()
    return value


def display_category_name(key: str) -> str:
    return key.lower().capitalize()


def parliamentarian_identity(row: Mapping[str, str]) -> tuple[str, str]:
    unit = clean_cell(row.get("unidad_ejecutora"))
    if unit:
        return f"senado_unidad_{unit}", "unidad_ejecutora"
    return f"nombre_{slugify(row.get('nombre_completo', ''))}", "nombre_completo"


def build_name_catalog(rows: Sequence[CsvRow]) -> dict[str, str]:
    names_by_id: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        parliamentarian_id, _source = parliamentarian_identity(row)
        name = clean_cell(row.get("nombre_completo"))
        if name:
            names_by_id[parliamentarian_id].append(name)
    return {key: choose_display_name(names) for key, names in names_by_id.items()}


def choose_display_name(names: Sequence[str]) -> str:
    counted = Counter(names)

    def score(name: str) -> tuple[int, int, int, str]:
        stripped = name.strip()
        has_lower = int(any(char.islower() for char in stripped))
        not_upper = int(not stripped.isupper())
        return (has_lower, not_upper, counted[name], stripped)

    selected = max(counted, key=score)
    return display_person_name(selected)


def display_person_name(value: str) -> str:
    cleaned = clean_cell(value)
    if cleaned.isupper():
        cleaned = cleaned.title()
    for particle in [" De ", " Del ", " La ", " Las ", " Los ", " Y "]:
        cleaned = cleaned.replace(particle, particle.lower())
    return cleaned


def parse_amount(value: str | None) -> int | None:
    cleaned = clean_cell(value)
    if not cleaned:
        return None
    if not re.fullmatch(r"-?\d+", cleaned):
        return None
    return int(cleaned)


def identity_signature(row: Mapping[str, str]) -> tuple[str, ...]:
    return (
        clean_cell(row.get("periodo")),
        clean_cell(row.get("unidad_ejecutora")),
        clean_cell(row.get("nombre_completo")),
        clean_cell(row.get("gastos_operacionales")),
        clean_cell(row.get("monto")),
    )


def collect_problem_example(
    examples: dict[str, list[dict[str, str]]],
    row_status: str,
    clean_row: CsvRow,
) -> None:
    if row_status == STATUS_OK or len(examples[row_status]) >= 10:
        return
    examples[row_status].append(
        {
            "source_id": clean_row["source_id"],
            "periodo": clean_row["periodo"],
            "parlamentario_nombre": clean_row["parlamentario_nombre"],
            "categoria_raw": clean_row["categoria_raw"],
            "monto_raw": clean_row["monto_raw"],
            "raw_file": clean_row["raw_file"],
        }
    )


def build_quality_report(
    *,
    source_path: Path | None,
    source_rows: Sequence[CsvRow],
    clean_rows: Sequence[CsvRow],
    ranking_rows: Sequence[CsvRow],
    category_rows: Sequence[CsvRow],
    row_status_counts: Counter[str],
    duplicate_source_ids: Counter[str],
    conflicting_duplicate_source_ids: set[str],
    missing_unit_count: int,
    amount_values: Sequence[int],
    problem_examples: Mapping[str, list[dict[str, str]]],
) -> dict[str, object]:
    periods = sorted({row["periodo"] for row in clean_rows if row["periodo"]})
    missing_periods = periods_missing_in_range(periods)
    included_rows = sum(1 for row in clean_rows if row["include_in_ranking"] == "true")
    zero_amounts = sum(1 for amount in amount_values if amount == 0)
    negative_amounts = sum(1 for amount in amount_values if amount < 0)
    duplicate_extra_rows = sum(duplicate_source_ids.values())

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source_path": "" if source_path is None else source_path.as_posix(),
        "source_rows": len(source_rows),
        "clean_rows": len(clean_rows),
        "included_in_ranking_rows": included_rows,
        "ranking_rows": len(ranking_rows),
        "category_rows": len(category_rows),
        "periods": {
            "count": len(periods),
            "min": periods[0] if periods else "",
            "max": periods[-1] if periods else "",
            "missing_in_range": missing_periods,
        },
        "amounts": {
            "numeric_rows": len(amount_values),
            "empty_or_invalid_rows": len(clean_rows) - len(amount_values),
            "zero_rows": zero_amounts,
            "negative_rows": negative_amounts,
            "positive_or_zero_total": sum(amount for amount in amount_values if amount >= 0),
            "negative_total": sum(amount for amount in amount_values if amount < 0),
        },
        "identity": {
            "missing_unidad_ejecutora_rows": missing_unit_count,
            "duplicate_source_id_groups": len(duplicate_source_ids),
            "duplicate_source_id_extra_rows": duplicate_extra_rows,
            "conflicting_duplicate_source_id_groups": len(conflicting_duplicate_source_ids),
            "conflicting_duplicate_source_id_examples": sorted(
                conflicting_duplicate_source_ids
            )[:10],
        },
        "row_status_counts": dict(sorted(row_status_counts.items())),
        "problem_examples": dict(problem_examples),
        "warnings": quality_warnings(
            duplicate_extra_rows=duplicate_extra_rows,
            conflicting_duplicate_source_ids=conflicting_duplicate_source_ids,
            missing_periods=missing_periods,
        ),
    }


def quality_warnings(
    *,
    duplicate_extra_rows: int,
    conflicting_duplicate_source_ids: set[str],
    missing_periods: Sequence[str],
) -> list[str]:
    warnings: list[str] = []
    if duplicate_extra_rows:
        warnings.append(
            "El CSV fuente contiene source_id duplicados. Re-ejecuta el scraper actualizado "
            "para recuperar paginas sin solapamiento antes de publicar rankings finales."
        )
    if conflicting_duplicate_source_ids:
        warnings.append("Hay source_id duplicados con contenido distinto; revisar fuente cruda.")
    if missing_periods:
        warnings.append("Hay periodos faltantes dentro del rango disponible.")
    return warnings


def enforce_quality_gate(
    report: Mapping[str, object],
    *,
    publication_from: str = DEFAULT_PUBLICATION_FROM,
) -> None:
    failures = quality_gate_failures(report, publication_from=publication_from)
    if not failures:
        print("Quality gate: ok")
        return

    formatted_failures = "\n".join(f"- {failure}" for failure in failures)
    raise SystemExit(
        "Quality gate failed; no se publicara ni cargara este run:\n"
        f"{formatted_failures}"
    )


def quality_gate_failures(
    report: Mapping[str, object],
    *,
    publication_from: str = DEFAULT_PUBLICATION_FROM,
) -> list[str]:
    try:
        publication_start = period_label(publication_from)
    except argparse.ArgumentTypeError as exc:
        return [str(exc)]

    failures: list[str] = []
    source_rows = report_int(report, "source_rows")
    clean_rows = report_int(report, "clean_rows")
    included_rows = report_int(report, "included_in_ranking_rows")
    ranking_rows = report_int(report, "ranking_rows")
    category_rows = report_int(report, "category_rows")
    periods = report_mapping(report, "periods")
    identity = report_mapping(report, "identity")
    row_status_counts = report_mapping(report, "row_status_counts")

    if source_rows == 0:
        failures.append("No hay filas fuente.")
    if clean_rows != source_rows:
        failures.append(
            f"Filas clean ({clean_rows}) no coinciden con filas fuente ({source_rows})."
        )
    if included_rows == 0:
        failures.append("No hay filas incluidas en ranking.")
    if ranking_rows == 0:
        failures.append("No hay filas de ranking.")
    if category_rows == 0:
        failures.append("No hay categorias normalizadas.")
    if report_int(periods, "count") == 0:
        failures.append("No hay periodos detectados.")

    missing_public_periods = publication_missing_periods(
        report_string_list(periods, "missing_in_range"),
        publication_from=publication_start,
    )
    if missing_public_periods:
        failures.append(
            "Hay periodos faltantes en el rango publico desde "
            f"{publication_start}: {format_period_sample(missing_public_periods)}."
        )

    duplicate_extra_rows = report_int(identity, "duplicate_source_id_extra_rows")
    if duplicate_extra_rows > 0:
        failures.append(f"Hay {duplicate_extra_rows} filas duplicadas por source_id.")

    conflicting_duplicates = report_int(identity, "conflicting_duplicate_source_id_groups")
    if conflicting_duplicates > 0:
        failures.append(
            f"Hay {conflicting_duplicates} grupos source_id duplicados con contenido distinto."
        )

    if report_int(row_status_counts, STATUS_OK) == 0:
        failures.append("No hay filas con row_status ok.")

    return failures


def publication_missing_periods(
    periods: Sequence[str],
    *,
    publication_from: str,
) -> list[str]:
    missing_periods: list[str] = []
    for period in periods:
        try:
            normalized_period = period_label(period)
        except argparse.ArgumentTypeError:
            missing_periods.append(period)
            continue
        if normalized_period >= publication_from:
            missing_periods.append(normalized_period)
    return missing_periods


def format_period_sample(periods: Sequence[str]) -> str:
    sample = ", ".join(periods[:10])
    if len(periods) <= 10:
        return sample
    return f"{sample} (+{len(periods) - 10} mas)"


def report_mapping(report: Mapping[str, object], key: str) -> dict[str, object]:
    value = report.get(key)
    if not isinstance(value, Mapping):
        return {}
    return {str(item_key): item_value for item_key, item_value in value.items()}


def report_string_list(report: Mapping[str, object], key: str) -> list[str]:
    value = report.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def report_int(report: Mapping[str, object], key: str) -> int:
    value = report.get(key)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdecimal():
            return int(stripped)
    return 0


def periods_missing_in_range(periods: Sequence[str]) -> list[str]:
    if not periods:
        return []
    start = period_to_index(periods[0])
    end = period_to_index(periods[-1])
    present = set(periods)
    return [
        index_to_period(index)
        for index in range(start, end + 1)
        if index_to_period(index) not in present
    ]


def period_label(value: str) -> str:
    cleaned = clean_cell(value)
    if not re.fullmatch(r"\d{4}-\d{2}", cleaned):
        msg = f"Periodo invalido {value!r}. Usa YYYY-MM."
        raise argparse.ArgumentTypeError(msg)

    month = int(cleaned[5:7])
    if not 1 <= month <= 12:
        msg = f"Mes invalido en periodo {value!r}. Usa 01-12."
        raise argparse.ArgumentTypeError(msg)

    return cleaned


def period_to_index(period: str) -> int:
    year_text, month_text = period.split("-", maxsplit=1)
    return int(year_text) * 12 + int(month_text) - 1


def index_to_period(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def normalize_ascii(value: str) -> str:
    cleaned = clean_cell(value)
    decomposed = unicodedata.normalize("NFD", cleaned)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def slugify(value: str) -> str:
    normalized = normalize_ascii(value).lower()
    slug = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return slug or "sin_valor"


def clean_cell(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\ufeff", "").strip())


def latest_csv(directory: Path, prefix: str) -> Path:
    path = optional_latest_csv(directory, prefix)
    if path is None:
        raise SystemExit(f"No se encontro CSV con prefijo {prefix!r} en {directory}")
    return path


def optional_latest_csv(directory: Path, prefix: str) -> Path | None:
    files = []
    for path in directory.glob(f"{prefix}*.csv"):
        if not is_normalizer_input_candidate(path, prefix):
            continue
        files.append(path)
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)


def is_normalizer_input_candidate(path: Path, prefix: str) -> bool:
    if not path.is_file():
        return False
    if prefix == EXPENSE_FILE_PREFIX and "parlamentarios" in path.name:
        return False
    return (
        "_por_ano" not in path.name
        and not path.name.endswith("periodos.csv")
        and "clean" not in path.name
        and "ranking" not in path.name
        and "categorias" not in path.name
    )


def suffix_from_expense_path(path: Path) -> str:
    stem = path.stem
    if stem.startswith(EXPENSE_FILE_PREFIX):
        return stem[len(EXPENSE_FILE_PREFIX) :]
    return stem


def read_csv(path: Path) -> list[CsvRow]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        return [dict(row) for row in csv.DictReader(file)]


def write_csv(path: Path, rows: Sequence[CsvRow], columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
