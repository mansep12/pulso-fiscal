# Pulso Fiscal

Plataforma de transparencia que recopila y visualiza gastos publicos asociados a autoridades, ministerios y servicios del Estado de Chile.

## Estado

En desarrollo inicial. Sin release publico todavia.

## Mision

Convertir datos publicos dificiles de revisar en informacion clara para cualquier ciudadano, con trazabilidad total a la fuente oficial.

## Principios

1. Todo dato publicado tiene URL fuente, fecha de captura y hash del documento.
2. Lenguaje tecnico, no acusatorio. Describir, no calificar.
3. Reproducibilidad: codigo abierto, metodologia publica y datos descargables.

## Licencias

- Codigo: MIT.
- Datos publicados: CC-BY-4.0.

## Estructura

- `etl/`: pipeline Python de descarga, parseo y normalizacion.
- `db/`: esquema PostgreSQL.
- `docs/`: metodologia, fuentes, glosario y decisiones.
- `web/`: frontend Next.js con datos demo mientras se valida la data real.

## Aviso

Las estimaciones, como litros o kilometros equivalentes, se presentan como rangos y no constituyen hechos absolutos. Para reportar errores o sugerir mejoras, abrir un issue.
