from pathlib import Path

import pytest

import pulso_fiscal.loaders.supabase as supabase_loader
from pulso_fiscal.loaders.supabase import load_pipeline, validate_pipeline_inputs
from pulso_fiscal.manifest import PipelineManifest, ProcessedFileRecord, sha256_file


def test_validate_pipeline_inputs_accepts_matching_manifest_and_csvs(tmp_path: Path) -> None:
    clean_path = write_csv(tmp_path / "clean.csv", rows=2)
    ranking_path = write_csv(tmp_path / "ranking.csv", rows=1)
    manifest = pipeline_manifest(clean_path, ranking_path, clean_rows=2, ranking_rows=1)

    validate_pipeline_inputs(manifest, clean_path, ranking_path)


def test_validate_pipeline_inputs_blocks_clean_row_count_mismatch(tmp_path: Path) -> None:
    clean_path = write_csv(tmp_path / "clean.csv", rows=1)
    ranking_path = write_csv(tmp_path / "ranking.csv", rows=1)
    manifest = pipeline_manifest(clean_path, ranking_path, clean_rows=2, ranking_rows=1)

    with pytest.raises(RuntimeError, match="CSV clean tiene 1 filas"):
        validate_pipeline_inputs(manifest, clean_path, ranking_path)


def test_validate_pipeline_inputs_blocks_invalid_manifest_period(tmp_path: Path) -> None:
    clean_path = write_csv(tmp_path / "clean.csv", rows=1)
    ranking_path = write_csv(tmp_path / "ranking.csv", rows=1)
    manifest = pipeline_manifest(
        clean_path,
        ranking_path,
        clean_rows=1,
        ranking_rows=1,
        period_from="2021-13",
    )

    with pytest.raises(RuntimeError, match="period_from invalido"):
        validate_pipeline_inputs(manifest, clean_path, ranking_path)


def test_validate_pipeline_inputs_blocks_missing_ranking_output(tmp_path: Path) -> None:
    clean_path = write_csv(tmp_path / "clean.csv", rows=1)
    ranking_path = write_csv(tmp_path / "ranking.csv", rows=1)
    manifest = pipeline_manifest(clean_path, ranking_path, clean_rows=1, ranking_rows=1)
    manifest.output_files = [
        record for record in manifest.output_files if record.name != "ranking_mensual"
    ]

    with pytest.raises(RuntimeError, match="Manifest sin output ranking_mensual"):
        validate_pipeline_inputs(manifest, clean_path, ranking_path)


def test_validate_pipeline_inputs_requires_public_manifest(tmp_path: Path) -> None:
    clean_path = write_csv(tmp_path / "clean.csv", rows=1)
    ranking_path = write_csv(tmp_path / "ranking.csv", rows=1)
    manifest = pipeline_manifest(clean_path, ranking_path, clean_rows=1, ranking_rows=1)
    manifest.public_manifest_url = ""

    with pytest.raises(RuntimeError, match="public_manifest_url"):
        validate_pipeline_inputs(manifest, clean_path, ranking_path)


def test_load_pipeline_validates_public_manifest_before_db_connection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clean_path = write_csv(tmp_path / "clean.csv", rows=1)
    ranking_path = write_csv(tmp_path / "ranking.csv", rows=1)
    manifest = pipeline_manifest(clean_path, ranking_path, clean_rows=1, ranking_rows=1)
    manifest.r2_manifest_key = ""
    called = False

    def fail_get_conn() -> None:
        nonlocal called
        called = True
        raise AssertionError("DB connection should not be opened")

    monkeypatch.setattr(supabase_loader, "_get_conn", fail_get_conn)

    with pytest.raises(RuntimeError, match="r2_manifest_key"):
        load_pipeline(manifest, clean_path, ranking_path)

    assert not called


def test_load_pipeline_validates_public_manifest_url_before_db_connection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clean_path = write_csv(tmp_path / "clean.csv", rows=1)
    ranking_path = write_csv(tmp_path / "ranking.csv", rows=1)
    manifest = pipeline_manifest(clean_path, ranking_path, clean_rows=1, ranking_rows=1)
    called = False

    def fail_public_manifest(_manifest: object) -> None:
        raise RuntimeError("manifest publico no alcanzable")

    def fail_get_conn() -> None:
        nonlocal called
        called = True
        raise AssertionError("DB connection should not be opened")

    monkeypatch.setattr(
        supabase_loader,
        "_validate_public_manifest_reachable",
        fail_public_manifest,
    )
    monkeypatch.setattr(supabase_loader, "_get_conn", fail_get_conn)

    with pytest.raises(RuntimeError, match="no alcanzable"):
        load_pipeline(manifest, clean_path, ranking_path)

    assert not called


def test_validate_pipeline_inputs_requires_https_public_manifest(tmp_path: Path) -> None:
    clean_path = write_csv(tmp_path / "clean.csv", rows=1)
    ranking_path = write_csv(tmp_path / "ranking.csv", rows=1)
    manifest = pipeline_manifest(clean_path, ranking_path, clean_rows=1, ranking_rows=1)
    manifest.public_manifest_url = "http://public.example/pipeline_manifest.json"

    with pytest.raises(RuntimeError, match="https"):
        validate_pipeline_inputs(manifest, clean_path, ranking_path)


def test_validate_pipeline_inputs_blocks_clean_sha256_mismatch(tmp_path: Path) -> None:
    clean_path = write_csv(tmp_path / "clean.csv", rows=1)
    ranking_path = write_csv(tmp_path / "ranking.csv", rows=1)
    manifest = pipeline_manifest(clean_path, ranking_path, clean_rows=1, ranking_rows=1)
    manifest.output_files[0].sha256 = "0" * 64

    with pytest.raises(RuntimeError, match="CSV clean tiene sha256"):
        validate_pipeline_inputs(manifest, clean_path, ranking_path)


def test_validate_pipeline_inputs_blocks_ranking_size_mismatch(tmp_path: Path) -> None:
    clean_path = write_csv(tmp_path / "clean.csv", rows=1)
    ranking_path = write_csv(tmp_path / "ranking.csv", rows=1)
    manifest = pipeline_manifest(clean_path, ranking_path, clean_rows=1, ranking_rows=1)
    manifest.output_files[1].size_bytes += 1

    with pytest.raises(RuntimeError, match="CSV ranking_mensual tiene"):
        validate_pipeline_inputs(manifest, clean_path, ranking_path)


def write_csv(path: Path, *, rows: int) -> Path:
    lines = ["id,value", *(f"{index},x" for index in range(rows))]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def pipeline_manifest(
    clean_path: Path,
    ranking_path: Path,
    *,
    clean_rows: int,
    ranking_rows: int,
    period_from: str = "2021-01",
    period_to: str = "2021-02",
) -> PipelineManifest:
    return PipelineManifest(
        dataset="senado_gastos_operacionales",
        source="Senado de Chile",
        run_id="20260605T000000Z",
        generated_at_utc="2026-06-05T00:00:00+00:00",
        period_from=period_from,
        period_to=period_to,
        download_manifest_path="",
        input_files=[],
        output_files=[
            ProcessedFileRecord(
                name="clean",
                local_path=str(clean_path),
                sha256=sha256_file(clean_path),
                size_bytes=clean_path.stat().st_size,
                row_count=clean_rows,
            ),
            ProcessedFileRecord(
                name="ranking_mensual",
                local_path=str(ranking_path),
                sha256=sha256_file(ranking_path),
                size_bytes=ranking_path.stat().st_size,
                row_count=ranking_rows,
            ),
        ],
        r2_manifest_key="senado/gastos_operacionales/runs/run/pipeline_manifest.json",
        public_manifest_url="https://public.example/pipeline_manifest.json",
    )
