# Fuente MVP

Objetivo: mantener una sola fuente clara para la primera version publica.

| Dataset | URL oficial | Estado | Formato usado | Periodo web | Observaciones |
| --- | --- | --- | --- | --- | --- |
| Gastos operacionales de senadores | https://www.senado.cl/transparencia/gastos-operacionales-senadores | revisada | API JSON publica consumida por la pagina | desde 2021-01 | La web usa solo registros rankeables del ultimo run ok. |

## Criterios

- Conservar URL fuente por request.
- Guardar fecha de captura UTC.
- Guardar hash SHA256 del body descargado.
- Mantener raw y processed fuera de Git.
- Cargar a Supabase solo datos normalizados y trazables.
