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

## Comandos futuros

Los comandos concretos se agregaran cuando exista el primer scraper piloto.
