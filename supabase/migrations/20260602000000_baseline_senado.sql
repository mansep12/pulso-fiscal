-- Baseline Senado MVP.
--
-- Esta migracion representa el estado actual correcto de la base para la web.
-- Es idempotente para poder registrarla aunque algunas piezas se hayan aplicado
-- manualmente antes de adoptar Supabase CLI.

-- ============================================================
-- dataset_runs
-- ============================================================
create table if not exists dataset_runs (
    id                  bigint primary key generated always as identity,
    dataset             text        not null,
    run_id              text        not null unique,
    generated_at_utc    timestamptz not null,
    period_from         text        not null,
    period_to           text        not null,
    row_count           integer     not null default 0,
    raw_r2_prefix       text        not null default '',
    processed_r2_prefix text        not null default '',
    manifest_r2_key     text        not null default '',
    public_manifest_url text        not null default '',
    status              text        not null default 'ok'
                            check (status in ('ok', 'error', 'partial')),
    created_at          timestamptz not null default now()
);

create index if not exists idx_dataset_runs_dataset on dataset_runs (dataset);
create index if not exists idx_dataset_runs_period_from on dataset_runs (period_from);
create index if not exists idx_dataset_runs_latest_ok
on dataset_runs (dataset, status, generated_at_utc desc, id desc);

-- ============================================================
-- senado_gastos_operacionales
-- ============================================================
create table if not exists senado_gastos_operacionales (
    id                      bigint primary key generated always as identity,
    run_id                  text        not null references dataset_runs (run_id) on delete cascade,
    source_id               text,
    row_number              integer,
    row_status              text,
    include_in_ranking      boolean     not null default false,
    exclusion_reason        text        not null default '',
    ano                     integer,
    mes                     integer,
    periodo                 text,
    parlamentario_id        text,
    parlamentario_nombre    text,
    parlamentario_id_source text,
    unidad_ejecutora        text,
    nombre_completo_raw     text,
    categoria_id            text,
    categoria_nombre        text,
    categoria_key           text,
    categoria_raw           text,
    monto                   bigint,
    monto_raw               text,
    source_url              text        not null default '',
    raw_file                text        not null default '',
    raw_body_sha256         text        not null default '',
    fecha_captura_utc       text        not null default '',
    created_at              timestamptz not null default now()
);

create index if not exists idx_sgo_run_id on senado_gastos_operacionales (run_id);
create index if not exists idx_sgo_periodo on senado_gastos_operacionales (periodo);
create index if not exists idx_sgo_parlamentario on senado_gastos_operacionales (parlamentario_id);
create index if not exists idx_sgo_categoria on senado_gastos_operacionales (categoria_key);
create index if not exists idx_sgo_ranking on senado_gastos_operacionales (include_in_ranking, periodo);
create index if not exists idx_sgo_latest_filters
on senado_gastos_operacionales (run_id, include_in_ranking, periodo);

-- ============================================================
-- senado_gastos_operacionales_ranking
-- ============================================================
create table if not exists senado_gastos_operacionales_ranking (
    id                   bigint primary key generated always as identity,
    run_id               text    not null references dataset_runs (run_id) on delete cascade,
    periodo              text    not null,
    ano                  integer not null,
    mes                  integer not null,
    categoria_id         text    not null,
    categoria_nombre     text    not null,
    parlamentario_id     text    not null,
    parlamentario_nombre text    not null,
    rank                 integer not null,
    total_monto          bigint  not null default 0,
    registros            integer not null default 0,
    total_ajustes        bigint  not null default 0,
    registros_ajuste     integer not null default 0,
    registros_sin_monto  integer not null default 0,
    registros_excluidos  integer not null default 0,
    created_at           timestamptz not null default now()
);

create index if not exists idx_sgor_run_id on senado_gastos_operacionales_ranking (run_id);
create index if not exists idx_sgor_periodo on senado_gastos_operacionales_ranking (periodo);
create index if not exists idx_sgor_parlamentario on senado_gastos_operacionales_ranking (parlamentario_id);
create index if not exists idx_sgor_categoria on senado_gastos_operacionales_ranking (categoria_id);
create index if not exists idx_sgor_latest_filters
on senado_gastos_operacionales_ranking (run_id, periodo, categoria_id, parlamentario_id);

-- ============================================================
-- Vistas latest
-- ============================================================
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
    mode() within group (order by categoria_nombre) as categoria_nombre,
    sum(total_monto)::bigint as total_monto,
    sum(registros)::integer as registros,
    count(distinct periodo)::integer as meses_con_datos,
    count(distinct parlamentario_id)::integer as parlamentarios
from senado_ranking_latest
group by categoria_id;

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

-- ============================================================
-- RPCs publicas usadas por la web
-- ============================================================
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
        mode() within group (order by ranking.categoria_nombre) as categoria_nombre,
        sum(ranking.total_monto)::bigint as total_monto,
        sum(ranking.registros)::integer as registros,
        count(distinct ranking.periodo)::integer as meses_con_datos
    from senado_ranking_latest ranking
    where ranking.parlamentario_id = p_parlamentario_id
      and (p_periodo_desde is null or p_periodo_desde = '' or ranking.periodo >= p_periodo_desde)
      and (p_periodo_hasta is null or p_periodo_hasta = '' or ranking.periodo <= p_periodo_hasta)
    group by ranking.categoria_id;
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
