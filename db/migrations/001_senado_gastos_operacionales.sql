-- Migration 001: schema inicial para gastos operacionales del Senado.
--
-- Aplicar en Supabase:
--   Dashboard -> SQL Editor -> pegar y ejecutar.
--
-- Tablas:
--   dataset_runs                       registro de cada corrida del pipeline
--   senado_gastos_operacionales        datos limpios fila a fila
--   senado_gastos_operacionales_ranking ranking mensual por parlamentario y categoria

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

create index if not exists idx_dataset_runs_dataset     on dataset_runs (dataset);
create index if not exists idx_dataset_runs_period_from on dataset_runs (period_from);

-- ============================================================
-- senado_gastos_operacionales
-- ============================================================
create table if not exists senado_gastos_operacionales (
    id                    bigint primary key generated always as identity,
    run_id                text        not null references dataset_runs (run_id) on delete cascade,
    source_id             text,
    row_number            integer,
    row_status            text,
    include_in_ranking    boolean     not null default false,
    exclusion_reason      text        not null default '',
    ano                   integer,
    mes                   integer,
    periodo               text,
    parlamentario_id      text,
    parlamentario_nombre  text,
    parlamentario_id_source text,
    unidad_ejecutora      text,
    nombre_completo_raw   text,
    categoria_id          text,
    categoria_nombre      text,
    categoria_key         text,
    categoria_raw         text,
    monto                 bigint,
    monto_raw             text,
    source_url            text        not null default '',
    raw_file              text        not null default '',
    raw_body_sha256       text        not null default '',
    fecha_captura_utc     text        not null default '',
    created_at            timestamptz not null default now()
);

create index if not exists idx_sgo_run_id          on senado_gastos_operacionales (run_id);
create index if not exists idx_sgo_periodo         on senado_gastos_operacionales (periodo);
create index if not exists idx_sgo_parlamentario   on senado_gastos_operacionales (parlamentario_id);
create index if not exists idx_sgo_categoria       on senado_gastos_operacionales (categoria_key);
create index if not exists idx_sgo_ranking         on senado_gastos_operacionales (include_in_ranking, periodo);

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

create index if not exists idx_sgor_run_id        on senado_gastos_operacionales_ranking (run_id);
create index if not exists idx_sgor_periodo       on senado_gastos_operacionales_ranking (periodo);
create index if not exists idx_sgor_parlamentario on senado_gastos_operacionales_ranking (parlamentario_id);
create index if not exists idx_sgor_categoria     on senado_gastos_operacionales_ranking (categoria_id);
