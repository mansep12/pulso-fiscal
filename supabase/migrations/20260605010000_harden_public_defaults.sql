-- Endurece privilegios publicos existentes y futuros sin ampliar la
-- superficie expuesta por la API.

-- ============================================================
-- Revokes sobre objetos existentes
-- ============================================================
revoke all privileges on all tables in schema public from PUBLIC, anon, authenticated;
revoke all privileges on all sequences in schema public from PUBLIC, anon, authenticated;
revoke execute on all functions in schema public from PUBLIC, anon, authenticated;

-- ============================================================
-- Revokes por defecto para objetos futuros creados por migraciones
-- ============================================================
alter default privileges for role postgres in schema public
revoke all privileges on tables from PUBLIC, anon, authenticated;

alter default privileges for role postgres in schema public
revoke all privileges on sequences from PUBLIC, anon, authenticated;

alter default privileges for role postgres in schema public
revoke execute on functions from PUBLIC, anon, authenticated;

-- ============================================================
-- Superficie publica explicita usada por la web
-- ============================================================
grant select on
    senado_latest_run,
    senado_gastos_latest,
    senado_ranking_latest,
    senado_period_range_latest,
    senado_resumen_senadores_latest,
    senado_categorias_latest,
    senado_periodos_latest
to anon, authenticated;

grant execute on function senado_resumen_senadores_filtrado(text, text, text, text)
to anon, authenticated;

grant execute on function senado_resumen_categorias_senador(text, text, text)
to anon, authenticated;

grant execute on function senado_resumen_periodos_senador(text, text, text)
to anon, authenticated;
