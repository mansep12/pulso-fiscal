from pathlib import Path

from pulso_fiscal.normalizers.senado_gastos_operacionales import (
    EXPENSE_FILE_PREFIX,
    STATUS_AJUSTE,
    STATUS_DUPLICADO,
    STATUS_MONTO_EN_TEXTO,
    STATUS_NOTA,
    classify_row,
    is_normalizer_input_candidate,
    normalize_category,
    normalize_expenses,
)


def test_normalize_category_merges_common_senado_variants() -> None:
    assert normalize_category("TRASLACION").id == "traslacion"
    assert normalize_category("TRASLACION SENADORES").id == "traslacion"
    assert normalize_category("TRASLACI\u00d3N").id == "traslacion"
    assert normalize_category("ARRIENDO OFICINAS").id == "arriendo_oficinas"
    assert normalize_category("ARRIENDO DE OFICINAS").id == "arriendo_oficinas"


def test_classify_row_marks_non_rankable_records() -> None:
    note_category = normalize_category("NOTA: SE UTILIZO REMANENTE")
    money_text_category = normalize_category("$ 1.379.565")
    regular_category = normalize_category("TRASLACION")

    assert (
        classify_row(
            {"gastos_operacionales": "NOTA: SE UTILIZO REMANENTE"},
            note_category,
            None,
            False,
        )
        == STATUS_NOTA
    )
    assert (
        classify_row(
            {"gastos_operacionales": "$ 1.379.565"},
            money_text_category,
            None,
            False,
        )
        == STATUS_MONTO_EN_TEXTO
    )
    assert (
        classify_row({"gastos_operacionales": "TRASLACION"}, regular_category, -10, False)
        == STATUS_AJUSTE
    )
    assert (
        classify_row({"gastos_operacionales": "TRASLACION"}, regular_category, 100, True)
        == STATUS_DUPLICADO
    )


def test_normalize_expenses_excludes_duplicates_and_builds_monthly_ranking() -> None:
    rows = [
        expense_row("1", "2025-01", "7", "Persona Uno", "TRASLACION", "100"),
        expense_row("2", "2025-01", "7", "Persona Uno", "TRASLACION SENADORES", "50"),
        expense_row("2", "2025-01", "7", "Persona Uno", "TRASLACION SENADORES", "50"),
        expense_row("3", "2025-01", "7", "Persona Uno", "TRASLACI\u00d3N", "25"),
        expense_row("4", "2025-01", "7", "Persona Uno", "TRASLACION", "-10"),
        expense_row("5", "2025-01", "7", "Persona Uno", "TRASLACION", ""),
    ]

    result = normalize_expenses(rows, source_path=Path("source.csv"))
    ranking_row = next(row for row in result.ranking_rows if row["categoria_id"] == "traslacion")

    assert ranking_row["total_monto"] == "175"
    assert ranking_row["registros"] == "3"
    assert ranking_row["total_ajustes"] == "-10"
    assert ranking_row["registros_sin_monto"] == "1"
    assert result.quality_report["identity"] == {
        "missing_unidad_ejecutora_rows": 0,
        "duplicate_source_id_groups": 1,
        "duplicate_source_id_extra_rows": 1,
        "conflicting_duplicate_source_id_groups": 0,
        "conflicting_duplicate_source_id_examples": [],
    }


def test_normalize_expenses_uses_stable_category_name_for_same_id() -> None:
    rows = [
        expense_row(
            "1",
            "2025-01",
            "7",
            "Persona Uno",
            "SUSCRIPCIONES DIARIOS Y REVISTAS",
            "100",
        ),
        expense_row(
            "2",
            "2025-01",
            "8",
            "Persona Dos",
            "SUSCRIPCIONES, DIARIOS Y REVISTAS",
            "200",
        ),
        expense_row(
            "3",
            "2025-02",
            "7",
            "Persona Uno",
            "SUSCRIPCIONES, DIARIOS Y REVISTAS",
            "300",
        ),
    ]

    result = normalize_expenses(rows, source_path=Path("source.csv"))
    category_names = {
        row["categoria_nombre"]
        for row in result.ranking_rows
        if row["categoria_id"] == "suscripciones_diarios_y_revistas"
    }

    assert category_names == {"Suscripciones diarios y revistas"}


def test_expense_autodiscovery_excludes_parliamentarian_csv(tmp_path: Path) -> None:
    expense_path = tmp_path / "senado_gastos_operacionales_2012-01_2026-02.csv"
    parliamentarian_path = (
        tmp_path / "senado_gastos_operacionales_parlamentarios_2012-01_2026-02.csv"
    )
    expense_path.write_text("", encoding="utf-8")
    parliamentarian_path.write_text("", encoding="utf-8")

    assert is_normalizer_input_candidate(
        expense_path,
        EXPENSE_FILE_PREFIX,
    )
    assert not is_normalizer_input_candidate(
        parliamentarian_path,
        EXPENSE_FILE_PREFIX,
    )


def expense_row(
    source_id: str,
    periodo: str,
    unidad_ejecutora: str,
    nombre_completo: str,
    categoria: str,
    monto: str,
) -> dict[str, str]:
    year, month = periodo.split("-")
    return {
        "source_id": source_id,
        "fuente": "senado",
        "dataset": "gastos-operacionales-senadores",
        "ano": year,
        "mes": str(int(month)),
        "periodo": periodo,
        "unidad_ejecutora": unidad_ejecutora,
        "nombre_completo": nombre_completo,
        "gastos_operacionales": categoria,
        "monto": monto,
        "source_url": "https://example.test",
        "raw_file": "raw.json",
        "raw_body_sha256": "abc",
        "fecha_captura_utc": "2026-01-01T00:00:00+00:00",
    }
