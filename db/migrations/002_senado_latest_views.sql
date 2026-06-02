-- Migration 002: vistas y funciones para el MVP Senado.
--
-- La web consume solo datos agregados del ultimo run ok, desde 2021-01.
-- Las vistas principales usan la tabla mensual de ranking para reducir costo.

create index if not exists idx_dataset_runs_latest_ok
on dataset_runs (dataset, status, generated_at_utc desc, id desc);

create index if not exists idx_sgo_latest_filters
on senado_gastos_operacionales (run_id, include_in_ranking, periodo);

create index if not exists idx_sgor_latest_filters
on senado_gastos_operacionales_ranking (run_id, periodo, categoria_id, parlamentario_id);

create or replace view senado_latest_run as
select
    id,
    dataset,
    run_id,
    generated_at_utc,
    period_from,
    period_to,
    row_count,
    public_manifest_url,
    status
from dataset_runs
where dataset = 'senado_gastos_operacionales'
  and status = 'ok'
order by generated_at_utc desc, id desc
limit 1;

create or replace view senado_gastos_latest as
select
    g.run_id,
    g.source_id,
    g.row_number,
    g.periodo,
    g.ano,
    g.mes,
    g.parlamentario_id,
    g.parlamentario_nombre,
    g.categoria_id,
    g.categoria_nombre,
    g.categoria_key,
    g.categoria_raw,
    g.monto,
    g.source_url,
    g.raw_file,
    g.raw_body_sha256,
    g.fecha_captura_utc
from senado_gastos_operacionales g
join senado_latest_run latest on latest.run_id = g.run_id
where g.include_in_ranking = true
  and g.periodo >= '2021-01';

create or replace view senado_ranking_latest as
select
    ranking.run_id,
    ranking.periodo,
    ranking.ano,
    ranking.mes,
    ranking.categoria_id,
    ranking.categoria_nombre,
    ranking.parlamentario_id,
    ranking.parlamentario_nombre,
    ranking.total_monto,
    ranking.registros,
    ranking.total_ajustes,
    ranking.registros_ajuste,
    ranking.registros_sin_monto,
    ranking.registros_excluidos
from senado_gastos_operacionales_ranking ranking
join senado_latest_run latest on latest.run_id = ranking.run_id
where ranking.periodo >= '2021-01'
  and ranking.registros > 0;

create or replace view senado_period_range_latest as
select
    min(periodo) as period_from,
    max(periodo) as period_to
from senado_ranking_latest;

create or replace view senado_resumen_senadores_latest as
select
    parlamentario_id,
    parlamentario_nombre,
    sum(total_monto)::bigint as total_monto,
    sum(registros)::integer as registros,
    count(distinct periodo)::integer as meses_con_datos,
    round(sum(total_monto)::numeric / nullif(count(distinct periodo), 0))::bigint
        as promedio_mensual
from senado_ranking_latest
group by parlamentario_id, parlamentario_nombre;

create or replace view senado_categorias_latest as
select
    categoria_id,
    categoria_nombre,
    sum(total_monto)::bigint as total_monto,
    sum(registros)::integer as registros,
    count(distinct periodo)::integer as meses_con_datos,
    count(distinct parlamentario_id)::integer as parlamentarios
from senado_ranking_latest
group by categoria_id, categoria_nombre;

create or replace view senado_periodos_latest as
select
    periodo,
    ano,
    mes,
    sum(total_monto)::bigint as total_monto,
    sum(registros)::integer as registros,
    count(distinct parlamentario_id)::integer as parlamentarios
from senado_ranking_latest
group by periodo, ano, mes;

create or replace function senado_resumen_senadores_filtrado(
    p_categoria_id text default null,
    p_periodo_desde text default '2021-01',
    p_periodo_hasta text default null,
    p_busqueda text default null
)
returns table (
    parlamentario_id text,
    parlamentario_nombre text,
    total_monto bigint,
    registros integer,
    meses_con_datos integer,
    promedio_mensual bigint
)
language sql
stable
as $$
    select
        ranking.parlamentario_id,
        ranking.parlamentario_nombre,
        sum(ranking.total_monto)::bigint as total_monto,
        sum(ranking.registros)::integer as registros,
        count(distinct ranking.periodo)::integer as meses_con_datos,
        round(sum(ranking.total_monto)::numeric / nullif(count(distinct ranking.periodo), 0))::bigint
            as promedio_mensual
    from senado_ranking_latest ranking
    where (p_categoria_id is null or p_categoria_id = '' or ranking.categoria_id = p_categoria_id)
      and (p_periodo_desde is null or p_periodo_desde = '' or ranking.periodo >= p_periodo_desde)
      and (p_periodo_hasta is null or p_periodo_hasta = '' or ranking.periodo <= p_periodo_hasta)
      and (
          p_busqueda is null
          or p_busqueda = ''
          or ranking.parlamentario_nombre ilike '%' || p_busqueda || '%'
      )
    group by ranking.parlamentario_id, ranking.parlamentario_nombre;
$$;

create or replace function senado_resumen_categorias_senador(
    p_parlamentario_id text,
    p_periodo_desde text default '2021-01',
    p_periodo_hasta text default null
)
returns table (
    categoria_id text,
    categoria_nombre text,
    total_monto bigint,
    registros integer,
    meses_con_datos integer
)
language sql
stable
as $$
    select
        ranking.categoria_id,
        ranking.categoria_nombre,
        sum(ranking.total_monto)::bigint as total_monto,
        sum(ranking.registros)::integer as registros,
        count(distinct ranking.periodo)::integer as meses_con_datos
    from senado_ranking_latest ranking
    where ranking.parlamentario_id = p_parlamentario_id
      and (p_periodo_desde is null or p_periodo_desde = '' or ranking.periodo >= p_periodo_desde)
      and (p_periodo_hasta is null or p_periodo_hasta = '' or ranking.periodo <= p_periodo_hasta)
    group by ranking.categoria_id, ranking.categoria_nombre;
$$;

create or replace function senado_resumen_periodos_senador(
    p_parlamentario_id text,
    p_periodo_desde text default '2021-01',
    p_periodo_hasta text default null
)
returns table (
    periodo text,
    ano integer,
    mes integer,
    total_monto bigint,
    registros integer,
    categorias integer
)
language sql
stable
as $$
    select
        ranking.periodo,
        ranking.ano,
        ranking.mes,
        sum(ranking.total_monto)::bigint as total_monto,
        sum(ranking.registros)::integer as registros,
        count(distinct ranking.categoria_id)::integer as categorias
    from senado_ranking_latest ranking
    where ranking.parlamentario_id = p_parlamentario_id
      and (p_periodo_desde is null or p_periodo_desde = '' or ranking.periodo >= p_periodo_desde)
      and (p_periodo_hasta is null or p_periodo_hasta = '' or ranking.periodo <= p_periodo_hasta)
    group by ranking.periodo, ranking.ano, ranking.mes
    order by ranking.periodo desc;
$$;

grant select on
    senado_latest_run,
    senado_gastos_latest,
    senado_ranking_latest,
    senado_period_range_latest,
    senado_resumen_senadores_latest,
    senado_categorias_latest,
    senado_periodos_latest
to anon, authenticated, service_role;

grant execute on function senado_resumen_senadores_filtrado(text, text, text, text)
to anon, authenticated, service_role;

grant execute on function senado_resumen_categorias_senador(text, text, text)
to anon, authenticated, service_role;

grant execute on function senado_resumen_periodos_senador(text, text, text)
to anon, authenticated, service_role;
