# Base de datos

Supabase/PostgreSQL es la fuente de verdad para la web del MVP Senado.

## Migraciones

- `migrations/001_senado_gastos_operacionales.sql`: tablas base para runs, datos limpios y ranking mensual.
- `migrations/002_senado_latest_views.sql`: vistas y funciones que consume la web, filtradas desde 2021-01 y usando el ultimo run `ok`.

## Flujo

1. Ejecutar ETL y normalizador.
2. Cargar datos limpios y ranking con `--load-db`.
3. Aplicar migraciones SQL en Supabase.
4. La web consulta vistas/RPC agregadas, no tablas completas.

## Regla principal

Guardar runs historicos esta permitido, pero la web siempre lee solo el ultimo run con `status = 'ok'`.
