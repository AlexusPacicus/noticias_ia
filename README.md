# Noticias IA -- Pipeline v0

> 🔒 **Estado: v0-frozen** — Arquitectura validada con datos dummy. No conecta fuentes reales.

Pipeline determinista construido con LangGraph para seleccionar y resumir items recientes sobre IA.

El objetivo de v0 **no es informar**. Es validar que la arquitectura del pipeline es estable, reproducible y que el contrato de entrada/salida se cumple de extremo a extremo con datos simulados.

---

## ¿Qué es v0?

- Una prueba de concepto arquitectonica.
- Un pipeline lineal de 7 nodos con responsabilidades aisladas.
- Un sistema donde el ranking y la seleccion son **completamente deterministas**.
- Un entorno que usa datos dummy en lugar de fuentes reales.
- Una base sobre la que medir estabilidad antes de conectar fuentes externas.

## ¿Qué NO es v0?

- No es un producto funcional. No consulta fuentes reales.
- No proporciona información actualizada ni fiable.
- No implementa búsqueda, parsing de contenido ni extracción de texto.
- No utiliza embeddings, RAG ni ningun mecanismo semántico.
- No detecta tendencias ni evalua calidad de los items.
- No ofrece personalización ni memoria entre ejecuciones.

---

## 📦 Pipeline

El grafo ejecuta los siguientes nodos en orden estrictamente secuencial:

```
collect_input -> validate_input -> fetch -> normalize -> rank -> select -> summarize
```

### 1. collect_input

Recibe el estado inicial y lo encapsula en `raw_input` para preservar la entrada original a lo largo del pipeline.

### 2. validate_input

Valida el contrato de entrada:

- `query`: cadena de texto con un minimo de 2 palabras.
- `time_window`: valor cerrado (`last_24h`, `last_3_days`, `last_7_days`, `last_30_days`).
- `top_k`: entero entre 1 y 10. Por defecto 5.

Cualquier violacion lanza un error (`INVALID_QUERY`, `INVALID_TIME_WINDOW`, `INVALID_TOP_K`) y detiene la ejecucion.

### 3. fetch

Obtiene los items candidatos. En v0 devuelve una lista dummy fija (papers, releases, news) sin consultar fuentes externas.

### 4. normalize

Unifica el formato de los items. En v0 es un passthrough: copia los items sin transformacion.

### 5. rank

Aplica el **Ranking A** (ver seccion siguiente) para ordenar los items de forma determinista.

### 6. select

Recorta la lista a los primeros `top_k` items segun el ranking. Si la lista resultante esta vacia, lanza `EMPTY_RESULTS`.

### 7. summarize

Unico nodo que utiliza un LLM. Genera para cada item dos campos:

- `idea_clave` (maximo 60 palabras): descripcion factual.
- `por_que_importa` (maximo 40 palabras): contexto factual breve.

Valida el schema de cada resumen. Si la respuesta del modelo no cumple el contrato, lanza `SUMMARY_SCHEMA_VIOLATION`.

---

## 🧱 Ranking A

El ranking es puramente determinista. No hay semantica, no hay ML, no hay scoring basado en contenido.

Criterios de ordenacion (en orden de prioridad):

| Prioridad | Criterio | Direccion |
|-----------|----------|-----------|
| 1 | `published_at` | Descendente (mas reciente primero) |
| 2 | Tipo (`kind`) | `release` > `paper` > `news` |
| 3 | `title` | Ascendente (alfabetico) |
| 4 | `link` | Ascendente (alfabetico) |

- Los items sin `published_at` se colocan al final.
- Los tie-breakers (`title`, `link`) garantizan un orden total y reproducible incluso cuando los criterios principales empatan.
- El campo `score` asignado es simplemente la posicion ordinal (1, 2, 3...), no un valor ponderado.

---

## 🧠 Rol del LLM

El LLM interviene **unicamente** en el nodo `summarize`.

- **Modelo**: Ollama (`gemma3:4b`), temperatura 0.1, formato JSON forzado.
- **Funcion**: transformacion de texto. Recibe titulo, tipo y fuente de cada item; devuelve `idea_clave` y `por_que_importa`.
- **Restricciones**:
  - No decide que items se incluyen.
  - No filtra ni reordena resultados.
  - No accede a informacion externa al item proporcionado.
  - No emite opiniones, predicciones ni comparativas.
- **Validacion**: cada resumen se valida contra el schema (campos presentes, tipos correctos, limites de palabras). Si falla, el pipeline se detiene.

---

## 🧪 Tests de estabilidad

Los tests (`tests/test_pipeline_stability.py`) validan que el pipeline es determinista en todo lo que no depende del LLM.

### Que comprueban

| Test | Validacion |
|------|------------|
| `test_order_is_identical` | Dos ejecuciones identicas producen los mismos titulos en el mismo orden. |
| `test_links_are_identical` | Los enlaces devueltos son identicos entre ejecuciones. |
| `test_results_within_top_k` | El numero de resultados no excede `top_k`. |
| `test_result_schema` | Cada resultado tiene `kind` valido, `title`, `idea_clave`, `por_que_importa` y `link` no vacios. |

### Por que son un gate

Estos tests funcionan como puerta de paso para avanzar de version. Si alguno falla, significa que el pipeline no es estable y no se debe continuar hacia v1. La premisa es que la redaccion del resumen puede variar levemente entre ejecuciones (por la naturaleza del LLM), pero el **conjunto de items, su orden y la estructura del resultado deben ser identicos**.

---

## 🚧 Fuera de alcance en v0

Las siguientes funcionalidades no estan implementadas ni simuladas:

- **Fuentes reales**: `fetch` devuelve datos dummy. No hay conexion a arXiv, blogs ni medios.
- **Busqueda**: el `query` se valida pero no se utiliza para filtrar items.
- **Parsing**: no se extrae contenido de URLs ni documentos.
- **RAG**: no hay embeddings, indices vectoriales ni recuperacion semantica.
- **Tendencias**: no se detectan patrones temporales ni temas emergentes.
- **Evaluacion de calidad**: no se mide la relevancia, rigor ni impacto de los items.
- **Normalizacion real**: `normalize` es un passthrough; no deduplica ni unifica formatos.
- **Persistencia**: no hay estado entre ejecuciones.

---

## ⚠️ Riesgos asumidos en v0

- **Datos dummy no representan la realidad.** El comportamiento del pipeline con datos reales puede diferir. Formatos, volumenes y casos borde no estan cubiertos.
- **El LLM no es determinista.** Aunque se usa temperatura baja (0.1), la redaccion puede variar entre ejecuciones. Los tests de estabilidad aceptan esta variacion solo en los campos generados por el modelo.
- **Modelo local limitado.** `gemma3:4b` es un modelo pequeno ejecutado via Ollama. La calidad de los resumenes no esta evaluada formalmente.
- **Ranking sin fecha real.** Los items dummy no incluyen `published_at`, por lo que el criterio principal del Ranking A (fecha) no se ejerce en v0.
- **Normalize es un no-op.** No se ha validado la logica de deduplicacion ni unificacion con datos heterogeneos.
- **Sin manejo de errores de red ni timeouts.** Al no haber llamadas externas, estos escenarios no se contemplan.
- **Cobertura de tests minima.** Los tests verifican estabilidad pero no cubren todos los errores del contrato ni casos limite.

---

## Siguientes pasos (v1)

1. **Conectar fuentes reales**: implementar `fetch` contra arXiv API y blogs oficiales (OpenAI, Google, Anthropic).
2. **Implementar normalize**: deduplicacion por enlace, unificacion de campos, manejo de formatos heterogeneos.
3. **Activar published_at**: parsear fechas reales para que el Ranking A ordene por fecha efectiva.
4. **Usar query en fetch**: filtrar items segun la consulta del usuario.
5. **Ampliar tests**: cubrir errores del contrato, edge cases, volumenes mayores y timeouts.
6. **Evaluar calidad de resumenes**: metricas basicas (adherencia al schema, longitud, factualidad respecto al titulo).
7. **Manejo de errores de red**: reintentos, timeouts y fallback en `fetch`.
8. **CI/CD**: ejecutar tests de estabilidad como gate automatico en cada cambio.

---

## Estructura del proyecto

```
noticias/
  run.py                  # Punto de entrada
  graph/
    graph.py              # Definicion del grafo LangGraph
    nodes/
      collect_input.py
      validate_input.py
      fetch.py
      normalize.py
      rank.py
      select.py
      summarize.py
  tests/
    test_pipeline_stability.py
  docs/
    disenyo.md            # Documento de diseno
```

---

## Ejecucion

```bash
python run.py
```

Requiere Ollama corriendo localmente con el modelo `gemma3:4b` disponible.

## Tests

```bash
pytest tests/
```
