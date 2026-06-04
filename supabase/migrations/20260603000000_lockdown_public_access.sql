-- Cierra el acceso publico directo a tablas base y mantiene publica solo la
-- superficie controlada de vistas/RPC usada por la web.

-- ============================================================
-- RLS y permisos de tablas base
-- ============================================================
alter table dataset_runs enable row level security;
alter table senado_gastos_operacionales enable row level security;
alter table senado_gastos_operacionales_ranking enable row level security;

revoke all on table dataset_runs from anon, authenticated;
revoke all on table senado_gastos_operacionales from anon, authenticated;
revoke all on table senado_gastos_operacionales_ranking from anon, authenticated;

revoke all on all sequences in schema public from anon, authenticated;

-- ============================================================
-- Superficie publica usada por la web
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
