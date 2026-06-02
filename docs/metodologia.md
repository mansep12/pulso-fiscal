# Metodologia

Esta pagina define como se recopilan, procesan y presentan los datos de Pulso Fiscal.

## Fuente de datos

El MVP usa solo gastos operacionales de senadores publicados por el Senado de Chile:

```text
https://www.senado.cl/transparencia/gastos-operacionales-senadores
```

El scraper consume la API publica que usa esa pagina y guarda una copia raw de cada respuesta.

Cada dato debe conservar:

- URL fuente.
- Fecha de captura.
- Dataset.
- Documento original o referencia al recurso original.
- Hash SHA256 del body descargado.
- Categoria asignada.

## Periodicidad

La carga se ejecuta manualmente por ahora. La web muestra datos desde 2021-01 hasta el ultimo periodo cargado en Supabase.

## Normalizacion

El pipeline transforma la API del Senado a un esquema canonico con al menos:

- Senador.
- Periodo.
- Categoria de gasto.
- Monto original.
- URL fuente.
- Archivo raw.
- Hash de la respuesta.
- Estado de calidad de la fila.

## Comparacion principal

El ranking por defecto usa promedio mensual para comparar senadores con distinta cantidad de meses publicados:

```text
promedio_mensual = total_monto / meses_con_datos
```

`meses_con_datos` cuenta meses donde el senador tiene al menos un registro rankeable.

## Filas excluidas

El normalizador excluye del ranking filas que no son seguras para agregar, por ejemplo:

- montos vacios o invalidos;
- notas sin monto agregable;
- montos incrustados en texto;
- ajustes negativos, reportados aparte;
- duplicados si aparecen en la fuente.


## Base de datos

Supabase es la fuente de verdad de la web. Next.js consulta vistas y funciones SQL agregadas, no tablas crudas completas.

## Limitaciones conocidas

- La fuente puede cambiar de URL o formato.
- Los datos publicados pueden estar incompletos o agregados.
- No todos los senadores aparecen durante la misma cantidad de meses.

## Correcciones

Los errores detectados deben corregirse de forma visible. Cada correccion debe registrar:

- Fecha.
- Dato corregido.
- Motivo.
- Fuente nueva o aclaracion usada.
- Impacto en metricas o alertas.
