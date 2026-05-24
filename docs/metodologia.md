# Metodologia

Esta pagina define como se recopilan, procesan y presentan los datos de Pulso Fiscal.

## Fuentes de datos

- Sitios oficiales de ministerios y servicios.
- Transparencia Activa.
- Documentos descargables publicados por organismos publicos.
- Otras fuentes publicas oficiales cuando sean necesarias y verificables.

Cada dato debe conservar:

- URL fuente.
- Fecha de captura.
- Institucion emisora.
- Documento original o referencia al recurso original.
- Hash SHA256 del documento cuando corresponda.
- Categoria asignada.

## Periodicidad

La periodicidad inicial dependera de la frecuencia de actualizacion de cada fuente oficial. La primera etapa prioriza recoleccion manual asistida por scripts y validacion antes de automatizar.

## Normalizacion

Los datos de origen pueden venir en HTML, PDF, Excel, CSV u otros formatos. El pipeline debe transformar cada fuente a un esquema canonico con al menos:

- Institucion.
- Periodo.
- Categoria de gasto.
- Monto original.
- Proveedor, si existe.
- Documento fuente.
- Nivel de confianza.

## Calculo de litros estimados

Los litros estimados se calculan como rango, no como punto unico:

```text
litros_min = monto_gastado / precio_maximo_litro_periodo
litros_max = monto_gastado / precio_minimo_litro_periodo
```

El precio de referencia debe provenir de una fuente oficial o publica verificable y debe quedar documentado.

## Calculo de kilometros estimados

Los kilometros estimados tambien se calculan como rango:

```text
km_min = litros_min * rendimiento_bajo_km_l
km_max = litros_max * rendimiento_alto_km_l
```

Los supuestos de rendimiento deben publicarse junto al calculo. Un ejemplo inicial conservador:

- Rendimiento bajo: 5 km/l.
- Rendimiento alto: 12 km/l.

Estos valores deben revisarse si se obtiene informacion oficial de tipo de vehiculo o kilometraje real.

## Alertas tecnicas

Las alertas no son acusaciones. Son indicadores generados por reglas publicadas.

Reglas iniciales propuestas:

- Gasto inusual: monto mayor a `Q3 + 1.5 * IQR` dentro de instituciones comparables.
- Aumento mensual relevante: variacion mayor a 200% respecto del mes anterior.
- Falta de respaldo: gasto publicado sin documento o URL verificable.
- Concentracion de proveedor: proveedor concentra mas de 80% del gasto de una categoria en 12 meses.

Cada alerta debe incluir:

- Tipo de alerta.
- Formula usada.
- Datos de entrada.
- Fuente oficial.
- Nivel de confianza.

## Niveles de confianza

| Nivel | Definicion |
| --- | --- |
| Alto | Dato directo desde documento oficial, con URL y hash. |
| Medio | Dato calculado desde fuente oficial con formula publicada. |
| Bajo | Dato incompleto, no estandarizado o pendiente de confirmacion. |

## Limitaciones conocidas

- Las fuentes pueden cambiar de URL o formato.
- Los datos publicados pueden estar incompletos o agregados.
- Las equivalencias en litros y kilometros son estimaciones.
- Un gasto asociado a una institucion no implica automaticamente uso personal por una autoridad.

## Correcciones

Los errores detectados deben corregirse de forma visible. Cada correccion debe registrar:

- Fecha.
- Dato corregido.
- Motivo.
- Fuente nueva o aclaracion usada.
- Impacto en metricas o alertas.
