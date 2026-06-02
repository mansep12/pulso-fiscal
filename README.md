# Pulso Fiscal

Plataforma de transparencia que recopila y visualiza gastos operacionales publicados por el Senado de Chile.

## Estado

MVP en desarrollo. El foco actual es el Senado, con datos desde 2021 en adelante.

## Mision

Convertir datos publicos dificiles de revisar en rankings y tablas comparables, con trazabilidad a la fuente oficial y lenguaje neutral.

## Principios

1. Todo dato publicado tiene URL fuente, fecha de captura y hash del documento.
2. Lenguaje tecnico, no acusatorio. Describir, no calificar.
3. Reproducibilidad: codigo abierto, metodologia publica y datos descargables.

## Licencias

- Codigo: MIT.
- Datos publicados: CC-BY-4.0.

## Estructura

- `etl/`: pipeline Python de descarga, normalizacion, manifiestos y carga.
- `db/`: migraciones PostgreSQL/Supabase.
- `docs/`: metodologia, fuentes, glosario y decisiones.
- `web/`: frontend Next.js conectado a vistas agregadas en Supabase.

## Aviso

Un monto alto no implica por si solo irregularidad. Los rankings son comparaciones tecnicas sobre datos publicos. Para reportar errores o sugerir mejoras, abrir un issue.
