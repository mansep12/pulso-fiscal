# ETL Pulso Fiscal

Pipeline para descargar, parsear, normalizar y calcular metricas sobre datos publicos usados por Pulso Fiscal.

## Requisitos

- Python 3.12 o superior.
- uv.
- Chromium para Playwright.

## Instalacion

Desde `etl/`:

```powershell
uv sync --group dev
uv run playwright install chromium
```

## Estructura de datos

- `data/raw/`: HTML, PDF, Excel u otros documentos originales descargados desde fuentes oficiales. No se versiona en Git.
- `data/interim/`: resultados intermedios de parseo. No se versiona en Git.
- `data/processed/`: CSVs normalizados listos para cargar o publicar. Se puede versionar si el archivo es pequeno y no contiene datos sensibles.

## Convencion de nombres

Usar nombres reproducibles y ordenables:

```text
{fuente}_{institucion}_{periodo}_{fecha_captura}.{extension}
```

Ejemplo:

```text
transparencia_mop_2025-01_2026-05-24.html
```

## Flujo esperado

1. Descargar fuente oficial y guardar copia en `data/raw/`.
2. Calcular hash SHA256 del documento.
3. Parsear a una estructura tabular intermedia.
4. Normalizar al esquema canonico.
5. Calcular metricas y alertas.
6. Exportar resultado a `data/processed/`.

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

Descargar todo lo disponible:

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
uv run senado-normalizar-gastos-operacionales
```

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
