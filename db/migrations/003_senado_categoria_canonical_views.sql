-- Migration 003: agrega categorias por id canonico en vistas/funciones.
--
-- Algunas variantes de texto del Senado normalizan al mismo categoria_id,
-- pero mantienen categoria_nombre distinto. Si se agrupa por ambos campos,
-- la web recibe opciones duplicadas con la misma key de React.

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

grant select on senado_categorias_latest to anon, authenticated, service_role;

grant execute on function senado_resumen_categorias_senador(text, text, text)
to anon, authenticated, service_role;
