-- Exploratory PostgreSQL schema.
--
-- This file is intentionally a draft. During the MVP, the source of truth is
-- the ETL output in CSV/JSON files. Move this into a real migration only after
-- the available public data shapes are known.

create extension if not exists pgcrypto;

create table institucion (
    id uuid primary key default gen_random_uuid(),
    nombre text not null,
    tipo text not null check (tipo in ('ministerio', 'subsecretaria', 'servicio', 'otro')),
    parent_id uuid references institucion(id),
    url_oficial text,
    url_transparencia text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (nombre, tipo)
);

create table autoridad (
    id uuid primary key default gen_random_uuid(),
    nombre text not null,
    cargo text not null,
    institucion_id uuid not null references institucion(id),
    periodo_inicio date,
    periodo_fin date,
    url_fuente text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table vehiculo (
    id uuid primary key default gen_random_uuid(),
    institucion_id uuid not null references institucion(id),
    patente text,
    identificador text,
    tipo text,
    marca text,
    modelo text,
    anio integer check (anio is null or anio between 1900 and 2100),
    asignacion text,
    autoridad_id uuid references autoridad(id),
    nivel_confianza text not null default 'bajo' check (nivel_confianza in ('alto', 'medio', 'bajo')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (patente is not null or identificador is not null)
);

create table documento (
    id uuid primary key default gen_random_uuid(),
    institucion_id uuid references institucion(id),
    titulo text,
    url_oficial text not null,
    tipo_archivo text,
    fecha_documento date,
    fecha_captura timestamptz not null default now(),
    sha256 text,
    storage_path text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (url_oficial, sha256)
);

create table gasto (
    id uuid primary key default gen_random_uuid(),
    institucion_id uuid not null references institucion(id),
    autoridad_id uuid references autoridad(id),
    vehiculo_id uuid references vehiculo(id),
    documento_id uuid references documento(id),
    fecha date,
    periodo text not null,
    categoria text not null check (
        categoria in (
            'combustible',
            'arriendo_vehiculos',
            'mantencion',
            'tag_peajes',
            'viajes',
            'viaticos',
            'asesores',
            'alimentacion',
            'telefonia',
            'compras_menores',
            'otro'
        )
    ),
    monto_clp bigint not null check (monto_clp >= 0),
    proveedor text,
    descripcion text,
    fuente_url text,
    nivel_confianza text not null default 'bajo' check (nivel_confianza in ('alto', 'medio', 'bajo')),
    raw_record jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table alerta (
    id uuid primary key default gen_random_uuid(),
    gasto_id uuid references gasto(id),
    institucion_id uuid references institucion(id),
    autoridad_id uuid references autoridad(id),
    tipo text not null,
    severidad text not null check (severidad in ('informativa', 'atencion', 'alta')),
    explicacion text not null,
    formula text not null,
    datos_entrada jsonb not null default '{}'::jsonb,
    nivel_confianza text not null default 'bajo' check (nivel_confianza in ('alto', 'medio', 'bajo')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index idx_institucion_tipo on institucion(tipo);
create index idx_autoridad_institucion on autoridad(institucion_id);
create index idx_vehiculo_institucion on vehiculo(institucion_id);
create index idx_gasto_institucion_periodo on gasto(institucion_id, periodo);
create index idx_gasto_categoria_periodo on gasto(categoria, periodo);
create index idx_gasto_documento on gasto(documento_id);
create index idx_alerta_institucion on alerta(institucion_id);
create index idx_alerta_tipo_severidad on alerta(tipo, severidad);

create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger trg_institucion_updated_at
before update on institucion
for each row execute function set_updated_at();

create trigger trg_autoridad_updated_at
before update on autoridad
for each row execute function set_updated_at();

create trigger trg_vehiculo_updated_at
before update on vehiculo
for each row execute function set_updated_at();

create trigger trg_documento_updated_at
before update on documento
for each row execute function set_updated_at();

create trigger trg_gasto_updated_at
before update on gasto
for each row execute function set_updated_at();

create trigger trg_alerta_updated_at
before update on alerta
for each row execute function set_updated_at();
