# noticias — v1

Sistema gobernado por contrato para seleccion y resumen de items recientes sobre IA a partir de fuentes reales y cerradas.

---

## 1. Que es el sistema

Dado un `query` y un `time_window`, el sistema selecciona y resume items recientes sobre IA a partir de fuentes reales y cerradas, produciendo un resultado determinista, reproducible y contractual.

El sistema prioriza y selecciona items mediante reglas mecanicas. El uso de LLM se limita a resumen de texto.

v1 tiene el objetivo de probar la arquitectura con datos reales de una unica fuente (arXiv `cs.AI`), comprobando la aparicion de bugs basicos y validando que el pipeline contractual funciona de extremo a extremo.

**No-objetivos de v1:**

- Optimizar relevancia o cobertura.
- Evaluar calidad cientifica o impacto.
- Detectar tendencias o patrones.
- Introducir scoring semantico, embeddings o ML.
- Ajustar el sistema mediante feedback.
- Corregir, reinterpretar o "mejorar" outputs del LLM.
- Deduplicar items.

---

## 2. Arquitectura — Pipeline contractual

El pipeline se ejecuta en orden fijo, total e inmutable:

```
collect_input
  -> validate_input
    -> fetch
      -> normalize
        -> rank
          -> select
            -> summarize
```

| Nodo             | Responsabilidad                                                                    |
|------------------|------------------------------------------------------------------------------------|
| `collect_input`  | Ingesta del input bruto del usuario. Sin validacion ni transformacion.              |
| `validate_input` | Validacion del contrato de input y aplicacion de defaults.                          |
| `fetch`          | Obtencion de items desde la fuente, parametrizada por `query` y `time_window`.     |
| `normalize`      | Mapeo de schema: garantiza presencia y tipo de campos contractuales.                |
| `rank`           | Ordenacion lexica determinista segun coincidencia entre query y contenido del item. |
| `select`         | Seleccion de los `top_k` items segun ranking.                                      |
| `summarize`      | Generacion de resumenes descriptivos mediante LLM.                                  |

**Reglas contractuales del pipeline:**

- Ningun nodo puede reordenar el pipeline, saltarse pasos ni reejecutar nodos anteriores.
- Un nodo solo consume outputs validados del nodo anterior.
- Alterar el numero de nodos, su orden o su responsabilidad implica nueva version del sistema.
- Cualquier ejecucion que no siga este orden es invalida.

### Contrato I/O

**Input (usuario):**

| Campo         | Tipo              | Restriccion                                  |
|---------------|-------------------|----------------------------------------------|
| `query`       | `string`          | Min. 2 palabras; sin operadores              |
| `time_window` | `enum` (cerrado)  | `last_24h` \| `last_3_days` \| `last_7_days` |
| `top_k`       | `int` (opcional)  | Rango `[1..10]`, default `5`                 |

**Output (schema cerrado):**

```json
{
  "topic": "string",
  "time_window": "string",
  "results": [
    {
      "title": "string",
      "idea_clave": "string (max 80 palabras)",
      "relacion_con_query": "string (max 30 palabras)",
      "link": "string"
    }
  ]
}
```

- `topic`: copia literal de `input_validated.query`, sin normalizacion ni transformacion.
- `time_window`: copia literal de `input_validated.time_window`.
- Max. `top_k` resultados.
- Orden contractual derivado del ranking lexico.
- Resumenes descriptivos; sin opinion ni comparativa.

### State (interfaz unica entre nodos)

Lista cerrada de campos permitidos en el State:

| Campo              | Crea             | Lee                |
|--------------------|------------------|--------------------|
| `input_raw`        | `collect_input`  | `validate_input`   |
| `input_validated`  | `validate_input` | todos posteriores  |
| `external_units`   | `fetch`          | `normalize`        |
| `normalized_items` | `normalize`      | `rank`             |
| `ranked_items`     | `rank`           | `select`           |
| `selected_items`   | `select`         | `summarize`        |
| `output`           | `summarize`      | --                 |
| `abort_reason`     | runtime          | --                 |

Cada campo tiene un unico creador. No puede ser modificado despues de su creacion. La lectura de un campo por un nodo no autorizado constituye violacion contractual. La aparicion de cualquier campo no listado constituye violacion contractual.

---

## 3. Principios contractuales

Los contratos del sistema v1 se rigen por los siguientes principios:

- **Inmutabilidad de decisiones.** Las decisiones tomadas en un nodo no pueden ser reinterpretadas ni corregidas por nodos posteriores.
- **Validacion estricta.** Todo input y output intermedio debe cumplir su contrato antes de avanzar. No se aplican correcciones automaticas. No existen degradaciones silenciosas.
- **Orden contractual.** El orden de los elementos en cualquier lista del State es contractual y no puede alterarse tras su creacion.
- **Abort dominante.** Si `abort_reason` existe, ningun campo posterior puede crearse y `output` no puede existir.
- **Exhaustividad.** Todo dato necesario para evaluar la correccion del resultado debe estar presente en el output final o ser deducible del contrato. Nunca de estado interno.
- **Versionado.** Cambiar invariantes, orden del pipeline o rol del LLM implica nueva version del sistema.

---

## 4. Rol del LLM

El LLM opera unicamente en el nodo `summarize`. Actua exclusivamente como transformador de texto.

**El LLM no puede:**

- Participar en ranking, seleccion o filtrado.
- Introducir scoring, relevancia, impacto o comparativas.
- Acceder a contexto externo o a otros items.
- Reordenar resultados.
- Corregir, reintentar o "mejorar" su propia salida.

**Contrato de salida del LLM:**

El output es valido solo si cumple el schema contractual:

- Campos presentes: `idea_clave`, `relacion_con_query`.
- Tipos correctos.
- Limites de longitud: `idea_clave` max 80 palabras, `relacion_con_query` max 30 palabras.
- No hay post-procesado semantico.

Si el output no cumple el schema: `SUMMARY_SCHEMA_VIOLATION`. Ante error: ABORT total, sin resultados parciales. No existen retries inteligentes ni degradacion silenciosa.

**Invariante:** El LLM no aporta criterio al sistema. Si se elimina el LLM, el conjunto y orden de resultados permanecen identicos.

**Implementacion v1:** Ollama con modelo `gemma3:4b`. Invocacion individual por item (1:1). El LLM recibe unicamente el item individual que esta siendo procesado; no recibe la lista completa ni contexto de otros items.

---

## 5. Determinismo

A igualdad de input y estado de fuentes, el sistema produce:

- El mismo conjunto de items.
- En el mismo orden.

La unica variacion permitida es la redaccion de los campos generados por el LLM.

**Nota de determinismo temporal:**

El determinismo del sistema v1 se garantiza unicamente a igualdad de:

- input del usuario
- artefactos exogenos versionados
- snapshot temporal de la fuente

El sistema **no** garantiza determinismo inter-ejecucion si la fuente externa modifica su contenido o metadatos.

**Mecanismo de ranking determinista:**

Normalizacion textual contractual:

```
tokens(x):
  1. Convertir a lowercase.
  2. Reemplazar cualquier caracter no [a-z0-9] por espacio.
  3. Split por espacios.
  4. Eliminar tokens vacios.
  5. Resultado: set (tokens unicos).
```

Score: `score(item) = |Q interseccion T|` donde `Q = tokens(query)` y `T = tokens(title + " " + content)`.

Orden total determinista:

```
1. score DESC
2. title ASC
3. link ASC
```

No existen empates irresolubles. Sin frecuencia, sin substring, sin stemming, sin fuzzy, sin stopwords, sin heuristicas.

---

## 6. Manejo de aborts

Ante cualquier violacion contractual o error no contemplado:

- La ejecucion se detiene.
- No se devuelven resultados parciales.
- El sistema falla de forma explicita y trazable.
- Los nodos senalizan abort lanzando excepcion (`ValueError`). El runtime escribe `abort_reason` en el State.

### Aborts operativos

| Codigo                                 | Origen           | Descripcion                                |
|----------------------------------------|------------------|--------------------------------------------|
| `EMPTY_INPUT_PAYLOAD`                  | `collect_input`  | Entrada nula o inexistente                 |
| `INVALID_QUERY`                        | `validate_input` | Query no cumple formato requerido          |
| `INVALID_TIME_WINDOW`                  | `validate_input` | Ventana temporal fuera de enum             |
| `INVALID_TOP_K`                        | `validate_input` | Valor fuera de rango `[1..10]`             |
| `FETCH_SOURCE_ERROR`                   | `fetch`          | Fuente no responde o devuelve error        |
| `FETCH_NOT_ITERABLE`                   | `fetch`          | Respuesta no es coleccion iterable         |
| `NORMALIZE_MISSING_TITLE`              | `normalize`      | Unidad sin title valido                    |
| `NORMALIZE_MISSING_LINK`               | `normalize`      | Unidad sin link valido                     |
| `NORMALIZE_MISSING_CONTENT`            | `normalize`      | Unidad sin content valido                  |
| `RANK_QUERY_EMPTY_AFTER_NORMALIZATION` | `rank`           | Query vacia tras normalizacion textual     |
| `SELECT_MISSING_RANKED_ITEMS`          | `select`         | ranked_items no existe o no es lista       |
| `SELECT_TOPK_INVALID`                  | `select`         | top_k no es entero o <= 0                  |
| `SUMMARY_LLM_RUNTIME_ERROR`            | `summarize`      | Error de invocacion del LLM               |
| `SUMMARY_SCHEMA_VIOLATION`             | `summarize`      | Schema de resumen no cumplido              |

### Aborts generales del sistema

Condiciones bajo las cuales el flujo v1 se considera invalido como sistema gobernado, independientemente de que pueda ejecutarse o producir resultados. No describen errores operativos, no se evaluan en runtime y no prescriben comportamiento de ejecucion.

**Abort 1 -- Perdida de determinismo estructural.**
Cualquier variacion no controlada en el conjunto o el orden de los items, incluida la dependencia de inferencias, supuestos implicitos o criterios no expresados contractualmente. El flujo se considera no reproducible ni auditable.

**Abort 2 -- Asuncion de criterio por parte del LLM.**
El LLM introduce decisiones o modificaciones estructurales (inclusion, exclusion, priorizacion, orden, inferencia o mejora implicita). Quedan excluidas las transformaciones textuales explicitamente declaradas y acotadas por contrato. El flujo pierde gobernanza y la separacion entre criterio humano y ejecucion automatica.

**Abort 3 -- Acoplamiento semantico entre componentes.**
Un componente requiere conocer, inferir o asumir decisiones internas, criterios o estados no contractuales de otro componente para operar correctamente. El flujo pierde composabilidad y versionado estable.

**Abort 4 -- Imposibilidad de validacion ex-post.**
Determinar si el resultado es correcto requiere inspeccionar decisiones internas, pasos intermedios o razonamiento no expresado en el output contractual. El flujo deja de ser auditable.

**Abort 5 -- Ambiguedad de responsabilidad.**
Un componente asume multiples responsabilidades, responsabilidades implicitas o un rol no delimitado contractualmente. El flujo pierde gobernanza y previsibilidad.

---

## 7. Artefactos exogenos

El sistema depende de un conjunto cerrado, explicito y versionado de artefactos exogenos.

**Propiedades:**

- No son input del usuario.
- No son configurables en runtime.
- Son de solo lectura.
- Cambian exclusivamente mediante nueva version del sistema.

**Fuente primaria unica (v1):**

| Fuente | Categoria |
|--------|-----------|
| arXiv  | `cs.AI`   |

**Exclusiones explicitas en v1:**

- Cualquier otra categoria de arXiv.
- Blogs oficiales.
- Medios periodisticos.
- Agregadores, newsletters y redes sociales.
- Fuentes dinamicas o no versionadas.

**Invariante:** A igualdad de input y artefactos exogenos, el sistema produce resultados deterministas y reproducibles.

**Regla de cambio:** Cualquier modificacion en los artefactos exogenos implica actualizacion explicita del contrato y nueva version del sistema. No existen excepciones temporales.

---

## 8. Como ejecutar

### Dependencias

```bash
pip install -r requirements.txt
```

Requiere [Ollama](https://ollama.com/) con el modelo `gemma3:4b` disponible localmente para el nodo `summarize`.

### Runtime oficial

El contrato de sistema v1 declara `run_real_pipeline.py` como runtime oficial. Este runtime ejecuta los nodos secuencialmente, captura `ValueError` como mecanismo de abort y escribe `abort_reason` en el State.

El archivo presente en el repositorio que implementa este patron es `run_pipeline.py`:

```bash
python run_pipeline.py
```

`graph.py` (LangGraph) es un artefacto legacy mantenido para compatibilidad. No implementa el mecanismo de abort contractual y no constituye el runtime de referencia para v1.

### Tests

```bash
# Tests unitarios (sin red ni LLM)
python -m pytest --ignore=tests/test_e2e.py --ignore=tests/test_summarize.py

# Tests con mock de LLM
python -m pytest tests/test_summarize.py

# Tests e2e (requieren arXiv + Ollama)
python -m pytest -m e2e
```

---

## 9. Que NO es este sistema

- No es un motor de busqueda.
- No es un sistema de recomendacion.
- No es un evaluador de calidad, relevancia o impacto.
- No es un detector de tendencias.
- No permite que el LLM filtre, reordene o descarte items.
- No corrige, reintenta ni "arregla" salidas invalidas del LLM.
- No degrada silenciosamente: ante violacion, ABORT.
- No deduplica items.
- No introduce scoring semantico, embeddings ni ML.
- No se ajusta mediante feedback.
- No aplica correcciones automaticas sobre outputs intermedios.
- No devuelve resultados parciales ante error.

---

## 10. Estado de version

- **Version:** v1
- **Estado:** **FROZEN**

Contratos congelados:

| Contrato                     | Estado  |
|------------------------------|---------|
| Contrato de Sistema v1       | FROZEN  |
| Contrato de State v1         | FROZEN  |
| Contrato collect_input       | FROZEN  |
| Contrato validate_input      | FROZEN  |
| Contrato fetch               | FROZEN  |
| Contrato normalize           | FROZEN  |
| Contrato rank                | FROZEN  |
| Contrato select              | FROZEN  |
| Contrato summarize           | FROZEN  |
| Contrato Prompt Summarize    | FROZEN  |

**Efectos del estado FROZEN:**

- El contrato v1 esta cerrado y congelado.
- No se permiten modificaciones. Cualquier cambio requiere nueva version (v2).
- El paso a FROZEN requiere que todos los gates de cierre esten satisfechos.
- Cualquier modificacion posterior al FROZEN invalida el estado y requiere nueva version (v2).

**Gates de cierre de version:**

- **Gate A -- Consistencia contractual:** El comportamiento observado del sistema esta completamente descrito por el contrato.
- **Gate B -- Determinismo:** Mismo input + mismos artefactos = mismo conjunto y orden de resultados en ejecuciones repetidas.
- **Gate C -- Rol del LLM:** Eliminar el LLM no altera seleccion, ranking ni orden. El LLM solo afecta a campos textuales descriptivos.
- **Gate D -- Cierre v1:** Artefactos exogenos cerrados y versionados. Pipeline congelado. Contrato refleja limites reales, no aspiracionales. Tests y gates documentados.

**Regla de avance:** v1 no se "mejora": se sustituye por v2.
