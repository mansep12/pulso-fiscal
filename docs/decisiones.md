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
- Ambito inicial: Senado de Chile.
- MVP: gastos operacionales de senadores.
- Periodo publico inicial: desde 2021-01 hasta el ultimo periodo cargado.

## Fuente de datos

- Pagina oficial de Transparencia Activa del Senado.
- Cada dato publicado debe tener URL fuente, fecha de captura y hash del documento original cuando exista archivo descargable.
- Los documentos crudos se almacenan fuera de Git.

## Editorial

- El proyecto mide y visualiza datos publicos; no acusa personas ni instituciones.
- Usar lenguaje tecnico, verificable y neutral.
- Mostrar rankings como comparaciones tecnicas, no como conclusiones legales.
- No publicar datos personales innecesarios como RUT, domicilio, telefono o informacion privada.
- Se pueden usar nombres de senadores porque son autoridades y la fuente es oficial.

## Datos sensibles

- Se pueden publicar cargos, instituciones y sueldos de autoridades cuando provengan de fuentes oficiales publicas.
- Para personal no autoridad, priorizar agregacion por unidad, cargo o institucion.
- No publicar informacion privada aunque aparezca accidentalmente en documentos fuente.

## Stack inicial

- ETL: Python 3.12, uv, httpx, Polars, Rich.
- Base de datos: Supabase/PostgreSQL.
- Web: Next.js, TypeScript y Tailwind CSS.
- Hosting futuro: Cloudflare Pages o Vercel.
- Archivos: Cloudflare R2 para respaldar raw/processed.

## Licencias

- Codigo: MIT.
- Datos publicados: CC-BY-4.0.

## Operacion

- Proyecto personal de tiempo libre.
- Sin Pull Requests externos en la primera etapa; se aceptan issues para errores o sugerencias.
- Primer objetivo operativo: ranking comparable de gastos operacionales de senadores desde 2021.
