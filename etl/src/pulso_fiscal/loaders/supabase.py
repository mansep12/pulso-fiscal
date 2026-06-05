"""Carga de datos procesados a Supabase/Postgres.

Usa psycopg2 para conexion directa y polars para leer los CSVs.
Lee DATABASE_URL desde variables de entorno (cargar dotenv antes de llamar).

Uso:
    from pulso_fiscal.loaders.supabase import load_pipeline
    load_pipeline(manifest, clean_path, ranking_path)
"""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl
import psycopg2
import psycopg2.extras

if TYPE_CHECKING:
    from pulso_fiscal.manifest import PipelineManifest, ProcessedFileRecord


PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _get_conn() -> psycopg2.extensions.connection:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url or database_url == "REEMPLAZAR":
        msg = "Variable de entorno DATABASE_URL no configurada. Revisa etl/.env.local."
        raise RuntimeError(msg)
    return psycopg2.connect(database_url)


def load_pipeline(
    manifest: PipelineManifest,
    clean_path: Path,
    ranking_path: Path,
) -> None:
    """Carga completa del pipeline: dataset_run + clean + ranking."""
    validate_pipeline_inputs(manifest, clean_path, ranking_path)
    conn = _get_conn()
    try:
        with conn:
            upsert_dataset_run(manifest, conn)
            load_clean_csv(clean_path, manifest.run_id, conn)
            load_ranking_csv(ranking_path, manifest.run_id, conn)
        print(f"Carga a Supabase completa. run_id={manifest.run_id}")
    finally:
        conn.close()


def validate_pipeline_inputs(
    manifest: PipelineManifest,
    clean_path: Path,
    ranking_path: Path,
) -> None:
    """Valida manifest y archivos antes de tocar la base de datos."""
    if not manifest.run_id.strip():
        raise RuntimeError("Manifest sin run_id.")

    _validate_period("period_from", manifest.period_from)
    _validate_period("period_to", manifest.period_to)
    if manifest.period_from > manifest.period_to:
        raise RuntimeError(
            "Manifest con rango de periodos invalido: "
            f"{manifest.period_from} > {manifest.period_to}."
        )

    clean_record = _manifest_record(manifest, "clean")
    ranking_record = _manifest_record(manifest, "ranking_mensual")
    if clean_record is None:
        raise RuntimeError("Manifest sin output clean.")
    if ranking_record is None:
        raise RuntimeError("Manifest sin output ranking_mensual.")

    _validate_csv_path("clean", clean_path)
    _validate_csv_path("ranking_mensual", ranking_path)
    _validate_row_count("clean", clean_path, clean_record.row_count)
    _validate_row_count("ranking_mensual", ranking_path, ranking_record.row_count)


def _manifest_record(
    manifest: PipelineManifest,
    name: str,
) -> ProcessedFileRecord | None:
    return next((record for record in manifest.output_files if record.name == name), None)


def _validate_period(label: str, value: str) -> None:
    if not PERIOD_RE.fullmatch(value):
        raise RuntimeError(f"Manifest con {label} invalido: {value!r}.")


def _validate_csv_path(label: str, path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"CSV {label} no existe: {path}.")
    if not path.is_file():
        raise RuntimeError(f"CSV {label} no es un archivo: {path}.")


def _validate_row_count(label: str, path: Path, expected: int) -> None:
    actual = _csv_data_row_count(path)
    if actual != expected:
        raise RuntimeError(
            f"CSV {label} tiene {actual} filas, pero el manifest declara {expected}."
        )


def _csv_data_row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _row in reader)


def upsert_dataset_run(
    manifest: PipelineManifest,
    conn: psycopg2.extensions.connection,
) -> None:
    """Inserta o actualiza el registro de la corrida en dataset_runs."""
    output_files = manifest.output_files
    clean_record = next((f for f in output_files if f.name == "clean"), None)
    row_count = clean_record.row_count if clean_record else 0

    sql = """
        insert into dataset_runs (
            dataset, run_id, generated_at_utc, period_from, period_to,
            row_count, raw_r2_prefix, processed_r2_prefix,
            manifest_r2_key, public_manifest_url, status
        ) values (
            %(dataset)s, %(run_id)s, %(generated_at_utc)s, %(period_from)s, %(period_to)s,
            %(row_count)s, %(raw_r2_prefix)s, %(processed_r2_prefix)s,
            %(manifest_r2_key)s, %(public_manifest_url)s, 'ok'
        )
        on conflict (run_id) do update set
            generated_at_utc    = excluded.generated_at_utc,
            period_from         = excluded.period_from,
            period_to           = excluded.period_to,
            row_count           = excluded.row_count,
            manifest_r2_key     = excluded.manifest_r2_key,
            public_manifest_url = excluded.public_manifest_url,
            status              = excluded.status
    """
    params = {
        "dataset": manifest.dataset,
        "run_id": manifest.run_id,
        "generated_at_utc": manifest.generated_at_utc,
        "period_from": manifest.period_from,
        "period_to": manifest.period_to,
        "row_count": row_count,
        "raw_r2_prefix": "",
        "processed_r2_prefix": "",
        "manifest_r2_key": manifest.r2_manifest_key,
        "public_manifest_url": manifest.public_manifest_url,
    }
    with conn.cursor() as cur:
        cur.execute(sql, params)
    print(f"  dataset_runs upserted: run_id={manifest.run_id}")


def load_clean_csv(
    path: Path,
    run_id: str,
    conn: psycopg2.extensions.connection,
) -> None:
    """Carga el CSV clean a senado_gastos_operacionales. Borra registros previos del run_id."""
    df = pl.read_csv(path, infer_schema_length=0)

    # Eliminar registros anteriores del mismo run_id para permitir idempotencia
    with conn.cursor() as cur:
        cur.execute("delete from senado_gastos_operacionales where run_id = %s", (run_id,))

    rows = df.to_dicts()
    if not rows:
        print("  senado_gastos_operacionales: sin filas para cargar.")
        return

    sql = """
        insert into senado_gastos_operacionales (
            run_id, source_id, row_number, row_status, include_in_ranking,
            exclusion_reason, ano, mes, periodo,
            parlamentario_id, parlamentario_nombre, parlamentario_id_source,
            unidad_ejecutora, nombre_completo_raw,
            categoria_id, categoria_nombre, categoria_key, categoria_raw,
            monto, monto_raw, source_url, raw_file, raw_body_sha256, fecha_captura_utc
        ) values %s
    """
    values = [
        (
            run_id,
            _str(r, "source_id"),
            _int(r, "row_number"),
            _str(r, "row_status"),
            _bool(r, "include_in_ranking"),
            _str(r, "exclusion_reason"),
            _int(r, "ano"),
            _int(r, "mes"),
            _str(r, "periodo"),
            _str(r, "parlamentario_id"),
            _str(r, "parlamentario_nombre"),
            _str(r, "parlamentario_id_source"),
            _str(r, "unidad_ejecutora"),
            _str(r, "nombre_completo_raw"),
            _str(r, "categoria_id"),
            _str(r, "categoria_nombre"),
            _str(r, "categoria_key"),
            _str(r, "categoria_raw"),
            _int(r, "monto"),
            _str(r, "monto_raw"),
            _str(r, "source_url"),
            _str(r, "raw_file"),
            _str(r, "raw_body_sha256"),
            _str(r, "fecha_captura_utc"),
        )
        for r in rows
    ]
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, values, page_size=500)
    print(f"  senado_gastos_operacionales: {len(values)} filas cargadas.")


def load_ranking_csv(
    path: Path,
    run_id: str,
    conn: psycopg2.extensions.connection,
) -> None:
    """Carga el CSV de ranking mensual a senado_gastos_operacionales_ranking."""
    df = pl.read_csv(path, infer_schema_length=0)

    with conn.cursor() as cur:
        cur.execute(
            "delete from senado_gastos_operacionales_ranking where run_id = %s", (run_id,)
        )

    rows = df.to_dicts()
    if not rows:
        print("  senado_gastos_operacionales_ranking: sin filas para cargar.")
        return

    sql = """
        insert into senado_gastos_operacionales_ranking (
            run_id, periodo, ano, mes,
            categoria_id, categoria_nombre,
            parlamentario_id, parlamentario_nombre,
            rank, total_monto, registros,
            total_ajustes, registros_ajuste,
            registros_sin_monto, registros_excluidos
        ) values %s
    """
    values = [
        (
            run_id,
            _str(r, "periodo"),
            _int(r, "ano"),
            _int(r, "mes"),
            _str(r, "categoria_id"),
            _str(r, "categoria_nombre"),
            _str(r, "parlamentario_id"),
            _str(r, "parlamentario_nombre"),
            _int(r, "rank"),
            _int(r, "total_monto"),
            _int(r, "registros"),
            _int(r, "total_ajustes"),
            _int(r, "registros_ajuste"),
            _int(r, "registros_sin_monto"),
            _int(r, "registros_excluidos"),
        )
        for r in rows
    ]
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, values, page_size=500)
    print(f"  senado_gastos_operacionales_ranking: {len(values)} filas cargadas.")


# ── helpers de conversion ────────────────────────────────────────────────────

def _str(row: dict[str, str | None], key: str) -> str:
    v = row.get(key)
    return v if v is not None else ""


def _int(row: dict[str, str | None], key: str) -> int | None:
    v = row.get(key)
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _bool(row: dict[str, str | None], key: str) -> bool:
    v = row.get(key, "")
    return str(v).strip().lower() in {"true", "1", "yes", "si"}
