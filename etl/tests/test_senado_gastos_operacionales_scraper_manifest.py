from pathlib import Path

from pulso_fiscal.scrapers.senado_gastos_operacionales import (
    Period,
    ScraperConfig,
    _build_download_manifest,
)


def test_download_manifest_includes_only_current_run_raw_files(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    current_available = write_json(raw_dir / "available_periods.json")
    current_parliamentarians = write_json(raw_dir / "parlamentarians_periods" / "2024-01.json")
    current_expenses = write_json(raw_dir / "expenses" / "2024-01" / "page_001.json")
    write_json(raw_dir / "expenses" / "2023-12" / "page_001.json")

    config = ScraperConfig(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        from_period=None,
        to_period=None,
        year=None,
        month=None,
        max_periods=None,
        timeout=30,
        sleep_seconds=0,
        run_id="20260605T000000Z",
    )

    manifest = _build_download_manifest(
        config,
        [Period(2024, 1)],
        [current_available, current_parliamentarians, current_expenses],
    )

    assert {Path(record.local_path).name for record in manifest.raw_files} == {
        "available_periods.json",
        "2024-01.json",
        "page_001.json",
    }


def write_json(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"data": []}\n', encoding="utf-8")
    return path
