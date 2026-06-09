# Runbook operativo

Checklist minimo para publicar o revertir datos del MVP.

## Publicar run Senado

1. Aplicar migraciones pendientes con `supabase db push --dry-run` y luego `supabase db push`.
2. Descargar raw con `uv run senado-gastos-operacionales --from 2021-01 --upload-r2` desde `etl/`.
3. Normalizar, subir processed/manifest y cargar DB con `uv run senado-normalizar-gastos-operacionales --upload-r2 --load-db`.
4. Confirmar que el quality gate termina en `Quality gate: ok`.
5. Confirmar que `dataset_runs.public_manifest_url` y `dataset_runs.manifest_r2_key` no quedan vacios.
6. Confirmar que el `pipeline_manifest.json` publico referencia el `run_id` y `r2_manifest_key` del `download_manifest.json`.
7. Revisar la web: rango de periodos, ranking, ficha de senador y paginas de error/not-found.

## Reglas de publicacion

- `--load-db` siempre requiere manifest publico; no hay bypass local.
- Un run `status = 'ok'` debe tener URL publica de manifest.
- Antes de abrir conexion a DB, el loader verifica que `public_manifest_url` sea alcanzable y coincida con el run local.
- El normalizador reutiliza el `run_id` del download manifest; no publicar runs con IDs desacoplados.
- Si falla Supabase, la web debe mostrar error de carga y no una lista vacia.
- Si el quality gate falla, no publicar ni cargar DB.

## Rollback

1. Identificar el `run_id` problematico en `dataset_runs`.
2. Cambiar su `status` a `error` o `partial` para sacarlo de `senado_latest_run`.
3. Verificar que la web vuelva al ultimo run `ok` anterior.
4. Si no hay run anterior valido, corregir el pipeline y publicar un nuevo run completo.

## Evidencia minima

- `run_id` publicado.
- Fecha UTC de captura/generacion.
- `public_manifest_url`.
- Hashes SHA256 de raw y processed.
- Reporte de calidad del run.
