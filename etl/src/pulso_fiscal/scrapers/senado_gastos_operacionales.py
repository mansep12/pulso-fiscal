"""Download Senado operational expense transparency data.

The public page at ``www.senado.cl`` uses these API endpoints internally. This
module keeps the raw API payloads and also emits flat CSV files for analysis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from pulso_fiscal.manifest import DownloadManifest, RawFileRecord, make_run_id, sha256_file
from pulso_fiscal.storage.r2 import R2Client

BASE_URL = "https://web-back.senado.cl/api/transparency"
AVAILABLE_PERIODS_URL = f"{BASE_URL}/available-periods"
PARLIAMENTARIANS_PERIODS_URL = f"{BASE_URL}/parlamentarians-periods"
EXPENSES_URL = f"{BASE_URL}/expenses/senator-Operational-expenses"
ENDPOINT_NAME = "gastos-operacionales-senadores"
SOURCE_NAME = "senado"
EXPENSE_PAGE_SIZE = 500
EXPENSE_SORT = "id:asc"

ETL_DIR = Path(__file__).resolve().parents[3]
DEFAULT_RAW_DIR = ETL_DIR / "data" / "raw" / "senado" / "gastos_operacionales"
DEFAULT_PROCESSED_DIR = ETL_DIR / "data" / "processed"

HEADERS = {
    "Accept": "application/json",
    "Origin": "https://www.senado.cl",
    "Referer": "https://www.senado.cl/",
    "User-Agent": "pulso-fiscal-etl/0.1 (+https://www.senado.cl/)",
}

JsonObject = dict[str, Any]
CsvRow = dict[str, str | int | float | bool | None]
HttpParamValue = str | int | float | bool | None
HttpParams = list[tuple[str, HttpParamValue]]

AVAILABLE_PERIOD_COLUMNS = [
    "fuente",
    "dataset",
    "source_id",
    "ano",
    "mes",
    "periodo",
    "endpoint",
    "url",
    "createdAt",
    "updatedAt",
    "selected",
    "source_url",
    "fecha_captura_utc",
    "raw_body_sha256",
    "raw_file",
]

PARLIAMENTARIAN_COLUMNS = [
    "fuente",
    "dataset",
    "ano",
    "mes",
    "periodo",
    "unidad_ejecutora",
    "nombre",
    "appaterno",
    "apmaterno",
    "nombre_completo",
    "source_url",
    "fecha_captura_utc",
    "raw_body_sha256",
    "raw_file",
    "api_status",
    "api_results",
]

EXPENSE_COLUMNS = [
    "fuente",
    "dataset",
    "source_id",
    "ano",
    "mes",
    "periodo",
    "unidad_ejecutora",
    "nombre",
    "appaterno",
    "apmaterno",
    "nombre_completo",
    "gastos_operacionales",
    "monto",
    "createdAt",
    "updatedAt",
    "publishedAt",
    "source_url",
    "fecha_captura_utc",
    "raw_body_sha256",
    "raw_file",
    "api_status",
    "api_results",
    "api_page",
    "api_page_size",
    "api_page_count",
    "api_total",
]


@dataclass(frozen=True, order=True)
class Period:
    """Year-month period available in the Senado transparency API."""

    year: int
    month: int

    @property
    def label(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    @classmethod
    def parse(cls, value: str) -> Period:
        try:
            year_text, month_text = value.split("-", maxsplit=1)
            period = cls(year=int(year_text), month=int(month_text))
        except ValueError as exc:
            msg = f"Invalid period {value!r}. Use YYYY-MM."
            raise argparse.ArgumentTypeError(msg) from exc

        if not 1 <= period.month <= 12:
            msg = f"Invalid month in period {value!r}. Use 01-12."
            raise argparse.ArgumentTypeError(msg)

        return period


@dataclass(frozen=True)
class ApiResponse:
    """HTTP response metadata plus parsed JSON body."""

    url: str
    status_code: int
    captured_at_utc: str
    body_sha256: str
    body: JsonObject


@dataclass(frozen=True)
class ScraperConfig:
    raw_dir: Path
    processed_dir: Path
    from_period: Period | None
    to_period: Period | None
    year: int | None
    month: int | None
    max_periods: int | None
    timeout: float
    sleep_seconds: float
    upload_r2: bool = False
    run_id: str = ""


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv(ETL_DIR / ".env.local")
    args = parse_args(argv)
    config = ScraperConfig(
        raw_dir=args.raw_dir,
        processed_dir=args.processed_dir,
        from_period=args.from_period,
        to_period=None if args.to_period == "latest" else Period.parse(args.to_period),
        year=args.year,
        month=args.month,
        max_periods=args.max_periods,
        timeout=args.timeout,
        sleep_seconds=args.sleep,
        upload_r2=args.upload_r2,
        run_id=make_run_id(),
    )

    console = Console()
    with httpx.Client(headers=HEADERS, timeout=config.timeout, follow_redirects=True) as client:
        run(client, config, console)

    return 0


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Descarga gastos operacionales de senadores desde la API publica del Senado."
    )
    parser.add_argument(
        "--from",
        dest="from_period",
        type=Period.parse,
        default=None,
        help="Periodo inicial en formato YYYY-MM. Por defecto usa el primero disponible.",
    )
    parser.add_argument(
        "--to",
        dest="to_period",
        default="latest",
        help="Periodo final en formato YYYY-MM, o 'latest'. Por defecto: latest.",
    )
    parser.add_argument("--year", type=int, default=None, help="Filtra un ano especifico.")
    parser.add_argument(
        "--month",
        type=int,
        default=None,
        help="Filtra un mes especifico. Requiere --year.",
    )
    parser.add_argument(
        "--max-periods",
        type=int,
        default=None,
        help="Limita la cantidad de periodos descargados. Util para pruebas.",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=DEFAULT_RAW_DIR,
        help=f"Directorio para JSON crudo. Por defecto: {DEFAULT_RAW_DIR}",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=DEFAULT_PROCESSED_DIR,
        help=f"Directorio para CSV procesado. Por defecto: {DEFAULT_PROCESSED_DIR}",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Timeout HTTP en segundos. Por defecto: 60.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.1,
        help="Pausa entre requests en segundos. Por defecto: 0.1.",
    )
    parser.add_argument(
        "--upload-r2",
        action="store_true",
        default=False,
        help="Sube archivos raw a Cloudflare R2 al finalizar la descarga.",
    )

    args = parser.parse_args(argv)
    validate_args(args)
    return args


def validate_args(args: argparse.Namespace) -> None:
    if args.month is not None and args.year is None:
        raise SystemExit("--month requiere --year")
    if args.month is not None and not 1 <= args.month <= 12:
        raise SystemExit("--month debe estar entre 1 y 12")
    if args.to_period != "latest":
        Period.parse(args.to_period)
    if args.max_periods is not None and args.max_periods < 1:
        raise SystemExit("--max-periods debe ser mayor que 0")
    if args.sleep < 0:
        raise SystemExit("--sleep no puede ser negativo")


def run(client: httpx.Client, config: ScraperConfig, console: Console) -> None:
    config.raw_dir.mkdir(parents=True, exist_ok=True)
    config.processed_dir.mkdir(parents=True, exist_ok=True)

    available_response = fetch_available_periods(client)
    available_raw_path = config.raw_dir / "available_periods.json"
    save_raw_response(available_raw_path, available_response)

    available_items = extract_data_items(available_response.body)
    available_periods = sorted({period_from_api_item(item) for item in available_items})
    selected_periods = select_periods(available_periods, config)

    if not selected_periods:
        raise RuntimeError("No hay periodos disponibles para los filtros solicitados.")

    console.print(
        "Descargando "
        f"{len(selected_periods)} periodos: {selected_periods[0].label} a "
        f"{selected_periods[-1].label}"
    )

    period_rows = build_available_period_rows(
        available_items=available_items,
        selected_periods=set(selected_periods),
        response=available_response,
        raw_path=available_raw_path,
        root_dir=ETL_DIR,
    )
    write_csv(
        period_rows,
        config.processed_dir / "senado_gastos_operacionales_periodos.csv",
        AVAILABLE_PERIOD_COLUMNS,
    )

    parliamentarian_rows: list[CsvRow] = []
    expense_rows: list[CsvRow] = []

    progress = Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )
    with progress:
        task_id = progress.add_task("Periodos", total=len(selected_periods))
        for period in selected_periods:
            period_parliamentarian_rows = fetch_parliamentarians_for_period(
                client=client,
                period=period,
                config=config,
            )
            parliamentarian_rows.extend(period_parliamentarian_rows)
            sleep(config.sleep_seconds)

            period_expense_rows = fetch_expenses_for_period(
                client=client,
                period=period,
                config=config,
            )
            expense_rows.extend(period_expense_rows)
            sleep(config.sleep_seconds)

            progress.advance(task_id)

    start_period = selected_periods[0].label
    end_period = selected_periods[-1].label
    suffix = f"{start_period}_{end_period}"

    write_csv(
        parliamentarian_rows,
        config.processed_dir / f"senado_gastos_operacionales_parlamentarios_{suffix}.csv",
        PARLIAMENTARIAN_COLUMNS,
    )
    parliamentarian_year_paths = write_csv_by_year(
        parliamentarian_rows,
        config.processed_dir / "senado_gastos_operacionales_parlamentarios_por_ano",
        "senado_gastos_operacionales_parlamentarios",
        PARLIAMENTARIAN_COLUMNS,
    )
    write_csv(
        expense_rows,
        config.processed_dir / f"senado_gastos_operacionales_{suffix}.csv",
        EXPENSE_COLUMNS,
    )
    expense_year_paths = write_csv_by_year(
        expense_rows,
        config.processed_dir / "senado_gastos_operacionales_por_ano",
        "senado_gastos_operacionales",
        EXPENSE_COLUMNS,
    )

    console.print(
        "Listo: "
        f"{len(expense_rows)} filas de gastos y "
        f"{len(parliamentarian_rows)} filas de parlamentarios-periodo. "
        f"Tambien se generaron {len(expense_year_paths)} CSVs de gastos por ano y "
        f"{len(parliamentarian_year_paths)} CSVs de parlamentarios por ano."
    )

    manifest = _build_download_manifest(config, selected_periods)
    manifest_path = config.processed_dir / "senado" / "gastos_operacionales" / "download_manifest.json"
    manifest.write(manifest_path)
    console.print(f"Manifest guardado: {display_path(manifest_path, ETL_DIR)}")

    if config.upload_r2:
        console.print("Subiendo archivos a Cloudflare R2...")
        _upload_raw_to_r2(manifest, config, console)
        manifest.write(manifest_path)
        console.print("Subida a R2 completa.")


def fetch_available_periods(client: httpx.Client) -> ApiResponse:
    params: HttpParams = [
        ("pagination[limit]", "1000"),
        ("filters[endpoint][$eq]", ENDPOINT_NAME),
    ]
    return fetch_json(client, AVAILABLE_PERIODS_URL, params=params)


def fetch_parliamentarians_for_period(
    client: httpx.Client,
    period: Period,
    config: ScraperConfig,
) -> list[CsvRow]:
    params: HttpParams = [("year", str(period.year)), ("month", str(period.month))]
    response = fetch_json(client, PARLIAMENTARIANS_PERIODS_URL, params=params)
    raw_path = config.raw_dir / "parlamentarians_periods" / f"{period.label}.json"
    save_raw_response(raw_path, response)

    rows: list[CsvRow] = []
    for item in extract_data_items(response.body):
        row = flatten_mapping(item)
        add_common_row_fields(row, response, raw_path, ETL_DIR)
        add_period(row)
        add_full_name(row)
        add_api_status(row, response)
        rows.append(row)

    return rows


def fetch_expenses_for_period(
    client: httpx.Client,
    period: Period,
    config: ScraperConfig,
) -> list[CsvRow]:
    rows: list[CsvRow] = []
    first_response = fetch_expense_page(client, period, page=1)
    first_raw_path = expense_raw_path(config, period, page=1)
    save_raw_response(first_raw_path, first_response)

    page_count = pagination_int(first_response.body, "pageCount") or 1
    expected_total = pagination_int(first_response.body, "total")
    rows.extend(build_expense_rows(first_response, first_raw_path))

    for page in range(2, page_count + 1):
        sleep(config.sleep_seconds)
        response = fetch_expense_page(client, period, page=page)
        raw_path = expense_raw_path(config, period, page=page)
        save_raw_response(raw_path, response)
        rows.extend(build_expense_rows(response, raw_path))

    if expected_total is not None and len(rows) != expected_total:
        msg = (
            f"Periodo {period.label}: se descargaron {len(rows)} filas, "
            f"pero la API informo {expected_total}."
        )
        raise RuntimeError(msg)

    validate_expense_identity(period, rows, expected_total)

    return rows


def fetch_expense_page(client: httpx.Client, period: Period, page: int) -> ApiResponse:
    params: HttpParams = [
        ("pagination[page]", str(page)),
        ("pagination[pageSize]", str(EXPENSE_PAGE_SIZE)),
        ("sort", EXPENSE_SORT),
        ("filters[ano][$eq]", str(period.year)),
        ("filters[mes][$eq]", str(period.month)),
    ]
    return fetch_json(client, EXPENSES_URL, params=params)


def validate_expense_identity(
    period: Period,
    rows: Sequence[CsvRow],
    expected_total: int | None,
) -> None:
    source_ids: list[str] = []
    missing_source_ids = 0
    for row in rows:
        source_id = row.get("source_id")
        if source_id is None or source_id == "":
            missing_source_ids += 1
            continue
        source_ids.append(str(source_id))

    if missing_source_ids:
        msg = f"Periodo {period.label}: {missing_source_ids} filas sin source_id."
        raise RuntimeError(msg)

    duplicate_source_ids = sorted(
        source_id for source_id, count in Counter(source_ids).items() if count > 1
    )
    if duplicate_source_ids:
        sample = ", ".join(duplicate_source_ids[:5])
        msg = (
            f"Periodo {period.label}: source_id duplicados tras paginar "
            f"({len(duplicate_source_ids)} grupos). Ejemplos: {sample}."
        )
        raise RuntimeError(msg)

    if expected_total is not None and len(source_ids) != expected_total:
        msg = (
            f"Periodo {period.label}: se obtuvieron {len(source_ids)} source_id unicos, "
            f"pero la API informo {expected_total}."
        )
        raise RuntimeError(msg)


def fetch_json(
    client: httpx.Client,
    url: str,
    params: HttpParams,
) -> ApiResponse:
    captured_at_utc = now_utc()
    response = client.get(url, params=params)
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise RuntimeError(f"Respuesta JSON inesperada desde {response.url}")

    parsed_body = cast(JsonObject, body)
    api_status = parsed_body.get("status")
    if api_status is not None and api_status != "ok":
        raise RuntimeError(f"La API respondio status={api_status!r} desde {response.url}")

    return ApiResponse(
        url=str(response.url),
        status_code=response.status_code,
        captured_at_utc=captured_at_utc,
        body_sha256=hashlib.sha256(response.content).hexdigest(),
        body=parsed_body,
    )


def save_raw_response(path: Path, response: ApiResponse) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_url": response.url,
        "status_code": response.status_code,
        "captured_at_utc": response.captured_at_utc,
        "body_sha256": response.body_sha256,
        "body": response.body,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_available_period_rows(
    available_items: Sequence[JsonObject],
    selected_periods: set[Period],
    response: ApiResponse,
    raw_path: Path,
    root_dir: Path,
) -> list[CsvRow]:
    rows: list[CsvRow] = []
    for item in available_items:
        row = flatten_api_item(item)
        add_common_row_fields(row, response, raw_path, root_dir)
        add_period(row)
        row["selected"] = period_from_row(row) in selected_periods
        rows.append(row)
    return rows


def build_expense_rows(response: ApiResponse, raw_path: Path) -> list[CsvRow]:
    rows: list[CsvRow] = []
    for item in extract_data_items(response.body):
        row = flatten_api_item(item)
        add_common_row_fields(row, response, raw_path, ETL_DIR)
        add_period(row)
        add_full_name(row)
        add_api_status(row, response)
        add_pagination(row, response)
        rows.append(row)
    return rows


def flatten_api_item(item: Mapping[str, Any]) -> CsvRow:
    row: CsvRow = {}
    source_id = item.get("id")
    if source_id is not None:
        row["source_id"] = coerce_csv_value(source_id)

    attributes = item.get("attributes")
    if isinstance(attributes, Mapping):
        row.update(flatten_mapping(attributes))

    for key, value in item.items():
        if key in {"id", "attributes"}:
            continue
        row[f"item_{key}"] = coerce_csv_value(value)

    return row


def flatten_mapping(item: Mapping[str, Any]) -> CsvRow:
    return {str(key): coerce_csv_value(value) for key, value in item.items()}


def coerce_csv_value(value: Any) -> str | int | float | bool | None:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def add_common_row_fields(
    row: CsvRow,
    response: ApiResponse,
    raw_path: Path,
    root_dir: Path,
) -> None:
    row["fuente"] = SOURCE_NAME
    row["dataset"] = ENDPOINT_NAME
    row["source_url"] = response.url
    row["fecha_captura_utc"] = response.captured_at_utc
    row["raw_body_sha256"] = response.body_sha256
    row["raw_file"] = display_path(raw_path, root_dir)


def add_api_status(row: CsvRow, response: ApiResponse) -> None:
    row["api_status"] = coerce_csv_value(response.body.get("status"))
    row["api_results"] = coerce_csv_value(response.body.get("results"))


def add_pagination(row: CsvRow, response: ApiResponse) -> None:
    pagination = pagination_mapping(response.body)
    row["api_page"] = coerce_csv_value(pagination.get("page"))
    row["api_page_size"] = coerce_csv_value(pagination.get("pageSize"))
    row["api_page_count"] = coerce_csv_value(pagination.get("pageCount"))
    row["api_total"] = coerce_csv_value(pagination.get("total"))


def add_period(row: CsvRow) -> None:
    period = period_from_row(row)
    row["periodo"] = period.label


def add_full_name(row: CsvRow) -> None:
    parts = [row.get("nombre"), row.get("appaterno"), row.get("apmaterno")]
    row["nombre_completo"] = " ".join(str(part).strip() for part in parts if part)


def extract_data_items(body: Mapping[str, Any]) -> list[JsonObject]:
    data = body.get("data")
    if isinstance(data, Mapping):
        nested_data = data.get("data")
        if isinstance(nested_data, list):
            return [cast(JsonObject, item) for item in nested_data if isinstance(item, dict)]
    if isinstance(data, list):
        return [cast(JsonObject, item) for item in data if isinstance(item, dict)]
    return []


def pagination_mapping(body: Mapping[str, Any]) -> Mapping[str, Any]:
    data = body.get("data")
    if not isinstance(data, Mapping):
        return {}
    meta = data.get("meta")
    if not isinstance(meta, Mapping):
        return {}
    pagination = meta.get("pagination")
    if not isinstance(pagination, Mapping):
        return {}
    return pagination


def pagination_int(body: Mapping[str, Any], key: str) -> int | None:
    value = pagination_mapping(body).get(key)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdecimal():
        return int(value)
    return None


def period_from_api_item(item: Mapping[str, Any]) -> Period:
    attributes = item.get("attributes")
    if not isinstance(attributes, Mapping):
        raise RuntimeError(f"Periodo sin attributes: {item}")

    return period_from_mapping(attributes)


def period_from_row(row: Mapping[str, object]) -> Period:
    return period_from_mapping(row)


def period_from_mapping(mapping: Mapping[str, object]) -> Period:
    year = parse_int_field(mapping, "ano")
    month = parse_int_field(mapping, "mes")
    return Period(year=year, month=month)


def parse_int_field(mapping: Mapping[str, object], key: str) -> int:
    value = mapping.get(key)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdecimal():
        return int(value)
    raise RuntimeError(f"Campo {key!r} ausente o invalido: {value!r}")


def select_periods(available_periods: Sequence[Period], config: ScraperConfig) -> list[Period]:
    selected = list(available_periods)

    if config.year is not None:
        selected = [period for period in selected if period.year == config.year]
    if config.month is not None:
        selected = [period for period in selected if period.month == config.month]
    if config.from_period is not None:
        selected = [period for period in selected if period >= config.from_period]
    if config.to_period is not None:
        selected = [period for period in selected if period <= config.to_period]
    if config.max_periods is not None:
        selected = selected[: config.max_periods]

    return selected


def write_csv(rows: Sequence[CsvRow], path: Path, preferred_columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = csv_fieldnames(rows, preferred_columns)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_csv_by_year(
    rows: Sequence[CsvRow],
    directory: Path,
    filename_prefix: str,
    preferred_columns: Sequence[str],
) -> list[Path]:
    rows_by_year: dict[int, list[CsvRow]] = {}
    for row in rows:
        year = parse_int_field(row, "ano")
        rows_by_year.setdefault(year, []).append(row)

    paths: list[Path] = []
    for year, year_rows in sorted(rows_by_year.items()):
        path = directory / f"{filename_prefix}_{year}.csv"
        write_csv(year_rows, path, preferred_columns)
        paths.append(path)

    return paths


def csv_fieldnames(rows: Sequence[CsvRow], preferred_columns: Sequence[str]) -> list[str]:
    row_columns = {column for row in rows for column in row}
    columns = [column for column in preferred_columns if column in row_columns or not rows]
    extra_columns = sorted(row_columns.difference(columns))
    return [*columns, *extra_columns]


def expense_raw_path(config: ScraperConfig, period: Period, page: int) -> Path:
    return config.raw_dir / "expenses" / period.label / f"page_{page:03d}.json"


def display_path(path: Path, root_dir: Path) -> str:
    try:
        return path.relative_to(root_dir).as_posix()
    except ValueError:
        return path.as_posix()


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def sleep(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)


def _build_download_manifest(
    config: ScraperConfig,
    selected_periods: list[Period],
) -> DownloadManifest:
    """Escanea raw_dir y construye el DownloadManifest con hashes de cada archivo."""
    raw_files: list[RawFileRecord] = []
    for json_path in sorted(config.raw_dir.rglob("*.json")):
        raw_files.append(
            RawFileRecord(
                local_path=display_path(json_path, ETL_DIR),
                sha256=sha256_file(json_path),
                size_bytes=json_path.stat().st_size,
            )
        )

    period_from = selected_periods[0].label if selected_periods else ""
    period_to = selected_periods[-1].label if selected_periods else ""

    return DownloadManifest(
        dataset="senado_gastos_operacionales",
        source="Senado de Chile",
        run_id=config.run_id,
        captured_at_utc=now_utc(),
        period_from=period_from,
        period_to=period_to,
        periods_downloaded=len(selected_periods),
        raw_files=raw_files,
    )


def _upload_raw_to_r2(
    manifest: DownloadManifest,
    config: ScraperConfig,
    console: Console,
) -> None:
    """Sube todos los archivos raw a R2 y actualiza el manifest con las keys."""
    import os
    r2 = R2Client()
    raw_bucket = os.environ.get("R2_RAW_BUCKET", "pulso-fiscal-raw")
    r2_prefix = f"senado/gastos_operacionales/runs/{config.run_id}/raw"

    for record in manifest.raw_files:
        local_path = ETL_DIR / record.local_path
        r2_key = f"{r2_prefix}/{record.local_path}"
        if not r2.object_exists(raw_bucket, r2_key):
            r2.upload_file(local_path, raw_bucket, r2_key)
            console.print(f"  Subido: {r2_key}")
        else:
            console.print(f"  Ya existe: {r2_key}")
        record.r2_key = r2_key
        record.r2_bucket = raw_bucket

    manifest_r2_key = f"senado/gastos_operacionales/runs/{config.run_id}/download_manifest.json"
    manifest.r2_manifest_key = manifest_r2_key
    manifest_bytes = (
        __import__("json").dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    r2.upload_bytes(manifest_bytes, raw_bucket, manifest_r2_key, "application/json")
    console.print(f"  Manifest subido: {manifest_r2_key}")


if __name__ == "__main__":
    raise SystemExit(main())
