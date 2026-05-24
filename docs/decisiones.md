# Decisiones iniciales

Este documento registra las decisiones base del proyecto para evitar cambios de alcance prematuros.

## Identidad

- Nombre: Pulso Fiscal.
- Slug del repo: `pulso-fiscal`.
- Repositorio: `https://github.com/mansep12/pulso-fiscal`.
- Rama principal: `main`.
- Visibilidad: publico.
- Dominio propio: diferido.

## Alcance

- Pais inicial: Chile.
- Ambito inicial: Gobierno Central.
- MVP: combustible y vehiculos.
- Plan B: viaticos y viajes si los datos de combustible no estan disponibles o no son comparables.
- No incluir municipios, gobiernos regionales ni otros paises en la primera etapa.

## Fuente de datos

- Prioridad inicial: datos publicados en Transparencia Activa y sitios oficiales.
- Cada dato publicado debe tener URL fuente, fecha de captura y hash del documento original cuando exista archivo descargable.
- Los documentos crudos se almacenan fuera de Git si son pesados o cambiantes.

## Editorial

- El proyecto mide y visualiza datos publicos; no acusa personas ni instituciones.
- Usar lenguaje tecnico, verificable y neutral.
- Mostrar estimaciones como rangos, no como hechos absolutos.
- No publicar datos personales innecesarios como RUT, domicilio, telefono o informacion privada.
- Evitar nombres de funcionarios no autoridades cuando no sean estrictamente necesarios.

## Datos sensibles

- Se pueden publicar cargos, instituciones y sueldos de autoridades cuando provengan de fuentes oficiales publicas.
- Para personal no autoridad, priorizar agregacion por unidad, cargo o institucion.
- No publicar informacion privada aunque aparezca accidentalmente en documentos fuente.

## Stack inicial

- ETL: Python 3.12, uv, Polars, Playwright, DuckDB.
- Base de datos: PostgreSQL, inicialmente compatible con Neon free tier.
- Web futura: Next.js, TypeScript, Tailwind CSS y shadcn/ui.
- Hosting futuro: Cloudflare Pages o Vercel.
- Archivos futuros: Cloudflare R2 si se requiere almacenar documentos.

## Licencias

- Codigo: MIT.
- Datos publicados: CC-BY-4.0.

## Operacion

- Proyecto personal de tiempo libre.
- Sin Pull Requests externos en la primera etapa; se aceptan issues para errores o sugerencias.
- Primer objetivo operativo: matriz de disponibilidad de datos y un pipeline reproducible para un ministerio piloto.
