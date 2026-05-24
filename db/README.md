# Base de datos

La primera etapa de Pulso Fiscal no depende de una base de datos en la nube.

## Estrategia inicial

1. Descargar fuentes oficiales a `etl/data/raw/`.
2. Parsear y normalizar datos a `etl/data/processed/`.
3. Usar DuckDB local para explorar CSVs y generar agregados.
4. Exponer datos a la web como JSON/CSV estaticos.

## Por que no Postgres todavia

Todavia no se con certeza que formatos, columnas y granularidad tienen las fuentes publicas.

## Archivos

- `schema.draft.sql`: borrador exploratorio de entidades posibles.

## Migrar a Postgres/Neon

Usar una base de datos en la nube cuando exista al menos una de estas necesidades:

- Busqueda dinamica por autoridad o institucion.
- Filtros combinados complejos.
- Actualizaciones automaticas frecuentes.
- API publica.
- Reportes ciudadanos o usuarios.
- Volumen grande de datos que haga incomodo publicar JSON/CSV estatico.
