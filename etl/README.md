# ETL Pulso Fiscal

Pipeline para descargar, normalizar, respaldar y cargar datos publicos del Senado usados por Pulso Fiscal.

## Requisitos

- Python 3.12 o superior.
- uv.

## Instalacion

Desde `etl/`:

```powershell
uv sync --group dev
```

## Estructura de datos

- `data/raw/`: respuestas JSON originales descargadas desde la fuente oficial. No se versiona en Git.
- `data/interim/`: resultados intermedios si se requieren. No se versiona en Git.
- `data/processed/`: CSVs normalizados listos para cargar a Supabase o respaldar en R2.

## Convencion de nombres

Usar nombres reproducibles y ordenables:

```text
{fuente}_{dataset}_{periodo}.{extension}
```

Ejemplo:

```text
senado_gastos_operacionales_2021-01_2026-02.csv
```

## Flujo esperado

1. Descargar fuente oficial y guardar copia en `data/raw/`.
2. Calcular hash SHA256 del documento.
3. Normalizar al esquema canonico.
4. Generar tablas de ranking y reporte de calidad.
5. Exportar resultado a `data/processed/`.
6. Cargar Supabase con `--load-db` cuando corresponda.

## Comandos

### Scraper Senado: gastos operacionales senadores

Descarga la informacion publicada en:

```text
https://www.senado.cl/transparencia/gastos-operacionales-senadores
```

El scraper usa la API publica que consume la pagina y guarda dos niveles de
datos:

- JSON crudo en `data/raw/senado/gastos_operacionales/`, con la respuesta
  completa de la API, URL fuente, fecha de captura y hash SHA256 del body.
- CSV normalizado en `data/processed/`, conservando todos los campos que entrega
  la API y agregando columnas de trazabilidad.

Descargar el rango usado por la web:

```powershell
uv run senado-gastos-operacionales --from 2021-01
```

Descargar todo lo disponible para auditoria historica:

```powershell
uv run senado-gastos-operacionales
```

Descargar un mes puntual:

```powershell
uv run senado-gastos-operacionales --year 2026 --month 2
```

Descargar un rango:

```powershell
uv run senado-gastos-operacionales --from 2025-01 --to 2025-12
```

Prueba rapida con el primer periodo disponible:

```powershell
uv run senado-gastos-operacionales --max-periods 1
```

Archivos procesados generados:

```text
data/processed/senado_gastos_operacionales_periodos.csv
data/processed/senado_gastos_operacionales_parlamentarios_{inicio}_{fin}.csv
data/processed/senado_gastos_operacionales_{inicio}_{fin}.csv
data/processed/senado_gastos_operacionales_parlamentarios_por_ano/*.csv
data/processed/senado_gastos_operacionales_por_ano/*.csv
```

El CSV principal mantiene campos como `source_id`, `ano`, `mes`,
`unidad_ejecutora`, `nombre`, `appaterno`, `apmaterno`,
`gastos_operacionales`, `monto`, `createdAt`, `updatedAt`, `publishedAt`,
`source_url`, `fecha_captura_utc`, `raw_body_sha256` y `raw_file`.

### Normalizador Senado: rankings de gastos operacionales

Genera tablas derivadas para la aplicacion sin sobrescribir el CSV fuente. La
normalizacion marca filas con problemas para que los rankings usen solo datos
seguros de agregar.

```powershell
uv run senado-normalizar-gastos-operacionales --upload-r2 --load-db
```

`--load-db` exige un manifest publico. No se permite cargar un run `ok` a
Supabase si antes no se subio el manifest a R2 y quedo disponible en
`public_manifest_url`; antes de abrir conexion a DB, el loader lee esa URL y
verifica que el JSON corresponda al run local. El normalizador reutiliza el
`run_id` del `download_manifest.json` generado por el scraper, por lo que la
trazabilidad raw y processed queda ligada al mismo run.

Tambien se puede indicar un CSV especifico:

```powershell
uv run senado-normalizar-gastos-operacionales --expenses-csv data/processed/senado_gastos_operacionales_2012-01_2026-02.csv
```

Archivos generados:

```text
data/processed/senado_gastos_operacionales_clean_{inicio}_{fin}.csv
data/processed/senado_gastos_operacionales_ranking_mensual_{inicio}_{fin}.csv
data/processed/senado_gastos_operacionales_categorias_{inicio}_{fin}.csv
data/processed/senado_gastos_operacionales_quality_{inicio}_{fin}.json
```

Reglas principales:

- `source_id` duplicados quedan marcados como `duplicado` y no entran al ranking.
- Montos vacios, notas y montos incrustados en texto quedan excluidos del ranking.
- Montos negativos quedan como `ajuste`; se reportan aparte y no suben el ranking bruto.
- Las categorias se agrupan con un catalogo canonico, por ejemplo `TRASLACION`,
  `TRASLACION SENADORES` y variantes con tilde quedan como `traslacion`.

Para revision manual, abrir los archivos dentro de
`data/processed/senado_gastos_operacionales_por_ano/`. El CSV completo puede
ser pesado para extensiones de VS Code.

## Publicacion y rollback

Flujo minimo para publicar un run:

1. Descargar raw desde la fuente oficial.
2. Normalizar y revisar el reporte de calidad.
3. Publicar archivos procesados y manifest en R2.
4. Cargar Supabase solo con manifest publico disponible.
5. Verificar en la web que el rango publicado y el ranking correspondan al run.

```powershell
uv run senado-gastos-operacionales --from 2021-01 --upload-r2
uv run senado-normalizar-gastos-operacionales --upload-r2 --load-db
```

El segundo comando falla si no existe `data/processed/senado/gastos_operacionales/download_manifest.json`
con `run_id` y `r2_manifest_key`.

Si se detecta un problema despues de publicar, marcar el run como no publicable
en Supabase (`dataset_runs.status = 'error'` o `partial`) o cargar nuevamente el
ultimo run valido. La web usa solo el ultimo run con `status = 'ok'`.
