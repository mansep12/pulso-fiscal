"""Manifest dataclasses y escritura para el pipeline de Pulso Fiscal.

Dos tipos de manifest:
- DownloadManifest: generado por el scraper. Documenta que se descargo,
  cuando y desde donde. Incluye hashes de cada archivo raw guardado.
- PipelineManifest: generado por el normalizador. Documenta que archivos
  entraron, que salio, hashes de cada output y metricas de calidad.
  Referencia al DownloadManifest para trazabilidad completa.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class RawFileRecord:
    """Registro de un archivo raw descargado."""

    local_path: str
    sha256: str
    size_bytes: int
    r2_key: str = ""
    r2_bucket: str = ""


@dataclass
class ProcessedFileRecord:
    """Registro de un archivo procesado generado por el normalizador."""

    name: str
    local_path: str
    sha256: str
    size_bytes: int
    row_count: int
    r2_key: str = ""
    r2_bucket: str = ""
    public_url: str = ""


@dataclass
class DownloadManifest:
    """Manifest generado por el scraper al finalizar la descarga."""

    dataset: str
    source: str
    run_id: str
    captured_at_utc: str
    period_from: str
    period_to: str
    periods_downloaded: int
    raw_files: list[RawFileRecord] = field(default_factory=list)
    r2_manifest_key: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


@dataclass
class PipelineManifest:
    """Manifest generado por el normalizador al finalizar el pipeline."""

    dataset: str
    source: str
    run_id: str
    generated_at_utc: str
    period_from: str
    period_to: str
    download_manifest_path: str
    input_files: list[str]
    input_file_records: list[ProcessedFileRecord] = field(default_factory=list)
    output_files: list[ProcessedFileRecord] = field(default_factory=list)
    quality_summary: dict[str, object] = field(default_factory=dict)
    r2_manifest_key: str = ""
    public_manifest_url: str = ""
    download_manifest_run_id: str = ""
    download_manifest_r2_key: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def sha256_file(path: Path) -> str:
    """Calcula el SHA256 de un archivo en disco."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def make_run_id() -> str:
    """Genera un run_id reproducible basado en timestamp UTC."""
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
