# Documento de Diseño — v2

## 0. Estado del documento

- Versión: v2
- Estado: FROZEN
- Alcance: Arquitectura, modelo de datos, politicas y decisiones congeladas

---

## 1. Alcance

v2 es un motor multi-fuente determinista para descubrimiento y resumen de papers tecnicos.

### 1.1 Capacidades incluidas

- 2 fuentes tecnicas: arXiv y HuggingFace Papers.
- Normalizacion a schema comun cross-source.
- Filtro temporal uniforme post-normalize.
- Deduplicacion estructural cross-source por `canonical_id`.
- Ranking BM25 determinista (implementacion propia, sin librerias externas).
- Summarization distribuida secuencial (map-reduce, sin paralelismo).
- Output trazable: cada resultado incluye `source` y `rank_position`.

### 1.2 Fuera de alcance

- SDK / serving / checkpointing.
- Insight transversal.
- Senales sociales (likes, upvotes).
- Deduplicacion semantica (embeddings, umbrales de similitud).
- Reranking por LLM.

---

## 2. Fuentes

### 2.1 Fuentes activas

| Fuente        | Identificador    | Endpoint                         |
|---------------|------------------|----------------------------------|
| arXiv         | `"arxiv"`        | arXiv API (`export.arxiv.org`)   |
| HuggingFace   | `"huggingface"`  | HuggingFace Daily Papers (unico endpoint estable) |

No se mezclan endpoints dentro de una misma fuente. Cada fuente usa exactamente un endpoint.

### 2.2 Prioridad congelada

```python
SOURCE_PRIORITY = ["arxiv", "huggingface"]
```

Esta prioridad se usa para:

- Resolver duplicados (conservar el primero segun orden determinista).
- Establecer el orden de concatenacion en merge.

---

## 3. Grafo v2

### 3.1 Topologia

```
collect_input
  -> validate_input
  -> fetch_router
       |-> fetch_arxiv
       |-> fetch_huggingface
       +-> merge_source_units
  -> normalize
  -> filter_by_time_window
  -> dedupe
  -> rank_bm25
  -> select
  -> summarize_map
  -> summarize_reduce
```

### 3.2 Descripcion de nodos

| Nodo                   | Responsabilidad                                                        |
|------------------------|------------------------------------------------------------------------|
| `collect_input`        | Recoge el input del usuario.                                           |
| `validate_input`       | Valida formato y aplica defaults.                                      |
| `fetch_router`         | Despacha fetch a cada fuente activa.                                   |
| `fetch_arxiv`          | Obtiene papers de arXiv. Produce `SourceUnit[]`.                       |
| `fetch_huggingface`    | Obtiene papers de HuggingFace Daily Papers. Produce `SourceUnit[]`.    |
| `merge_source_units`   | Concatena y ordena las unidades de todas las fuentes. Evalua fallo global. |
| `normalize`            | Mapea `SourceUnit[]` a items normalizados con schema comun.            |
| `filter_by_time_window`| Aplica ventana temporal uniforme sobre `published_at`.                 |
| `dedupe`               | Elimina duplicados cross-source por `canonical_id`.                    |
| `rank_bm25`            | Ordena items por BM25 contra la query. Asigna `rank_position`.        |
| `select`               | Selecciona los primeros `effective_k` items.                           |
| `summarize_map`        | Genera summary por item (secuencial). Subgrafo: `summarize_one` + `validate_summary_schema`. |
| `summarize_reduce`     | Reordena resultados por `rank_position`. Construye output publico final. No usa LLM. |

---

## 4. Politica de fallo

### 4.1 Fetch (degradacion controlada)

- Si una fuente falla (error de red o respuesta invalida) -> continuar con las demas.
- Si todas las fuentes fallan -> abort `FETCH_ALL_SOURCES_FAILED`.
- Una fuente puede devolver 0 items sin considerarse fallo.

### 4.2 Items defectuosos en normalize

- Items con campos faltantes o invalidos se descartan.
- No se produce abort global por defectos parciales.

### 4.3 Filtro temporal

- Si tras `filter_by_time_window` no quedan items -> abort `NO_ITEMS_IN_TIME_WINDOW`.

### 4.4 Summarize (tolerancia parcial)

El subgrafo de summarize es tolerante a fallos individuales.

- Si un summary individual falla (error de LLM o violacion de schema):
  - El item se descarta del output final.
  - Se registra el fallo internamente.
  - No se produce abort inmediato.

- Si al menos un summary es valido -> continuar.

- Si todos los summaries fallan -> abort `SUMMARY_ALL_ITEMS_FAILED`.

No se recalculan posiciones de ranking.
Los `rank_position` originales se preservan para trazabilidad.

---

## 5. Modelo de datos interno

### 5.1 SourceUnit (crudo, por fuente)

Cada nodo `fetch_*` produce una lista de `SourceUnit`:

| Campo        | Tipo   | Descripcion                                        |
|--------------|--------|----------------------------------------------------|
| `source`     | `str`  | Identificador de fuente (`"arxiv"` o `"huggingface"`) |
| `source_seq` | `int`  | Contador incremental por fuente (0-indexed)        |
| `fetched_at` | `str`  | Timestamp ISO 8601 UTC del momento de fetch        |
| `payload`    | `dict` | Datos crudos serializables. Estructura heterogenea por fuente |

### 5.2 Merge determinista

`merge_source_units` realiza:

1. Concatenar las unidades de todas las fuentes.
2. Ordenar de forma determinista por: `(SOURCE_PRIORITY.index(source), source_seq)`.
3. Evaluar fallo global:
   - Si todas las fuentes fallaron -> abort `FETCH_ALL_SOURCES_FAILED`.
   - Si al menos una fuente produjo resultados -> continuar.

### 5.3 Item normalizado

Cada item normalizado contiene:

| Campo          | Tipo       | Descripcion                                       |
|----------------|------------|---------------------------------------------------|
| `title`        | `str`      | Titulo limpio (texto plano)                       |
| `content`      | `str`      | Contenido/abstract limpio (texto plano)           |
| `published_at` | `str`      | Fecha de publicacion normalizada (ISO 8601 UTC)   |
| `link`         | `str`      | URL del paper                                     |
| `source`       | `str`      | Fuente de origen                                  |
| `canonical_id` | `str`      | Identificador canonico para dedupe (ver seccion 6)|

---

## 6. canonical_id

Definicion formal congelada para la generacion de identificadores canonicos.

### 6.1 Regla 1 — Paper con arXiv ID

Si el item contiene un arXiv ID (en link o metadata):

1. Extraer arXiv ID con patron regex.
2. Detectar formato `YYYY.NNNNN` con posible sufijo de version `vN`.
3. Eliminar version.
4. Construir: `canonical_id = "arxiv:" + base_id`.

Ejemplo: `2401.12345v3` -> `arxiv:2401.12345`.

### 6.2 Regla 2 — HuggingFace apunta a arXiv

Si un item de HuggingFace incluye link o `arxiv_id` que referencia un paper de arXiv:

- Aplicar Regla 1.

### 6.3 Regla 3 — Item sin arXiv ID

Si no se puede derivar un arXiv ID:

1. Normalizar URL:
   - Convertir a lowercase.
   - Eliminar trailing slash.
   - Eliminar parametros `utm_*` (y solo esos).
   - No resolver redirects.
2. Construir: `canonical_id = "url:" + normalized_url`.

### 6.4 Prohibiciones

No se permite usar para `canonical_id`:

- Titulo.
- Contenido.
- Similitud semantica.
- Senales sociales.

---

## 7. Normalize

### 7.1 Responsabilidades

El nodo `normalize` transforma `merged_source_units` en items normalizados. Debe:

- Extraer `title`.
- Extraer `content`.
- Extraer o derivar `published_at` (datetime normalizado, ISO 8601 UTC).
- Limpiar HTML.
- Eliminar markdown.
- Normalizar espacios (resultado: texto plano limpio).
- Mantener `link`.
- Mantener `source`.
- Generar `canonical_id` (segun seccion 6).

### 7.2 Items defectuosos

- Items con campos obligatorios faltantes o invalidos se descartan.
- No se produce abort global por defectos parciales.

### 7.3 Prohibiciones

El nodo `normalize` no puede realizar:

- Ranking.
- Dedupe.
- Ordenacion.
- Heuristicas semanticas.

---

## 8. filter_by_time_window

### 8.1 Proposito

Aplicar ventana temporal uniforme cross-source usando `published_at` normalizado.

### 8.2 Comportamiento

- Input: `normalized_items` (cada uno con `published_at`).
- Output: `filtered_items`.
- Ventanas validas: `last_24h`, `last_3_days`, `last_7_days`.

### 8.3 Reglas

- Si un item no tiene `published_at` valido -> descartar item (no abort).
- Si `len(filtered_items) == 0` -> abort `NO_ITEMS_IN_TIME_WINDOW`.

---

## 9. Dedupe

### 9.1 Mecanismo

- Dedupe estricto por `canonical_id`.
- Input: `filtered_items`.
- Output: `deduped_items`.
- Si `len(deduped_items) == 0` -> abort `NO_ITEMS_AFTER_DEDUPE`.

### 9.2 Resolucion de duplicados

Ante duplicados, conservar el primero segun el orden determinista heredado de merge:

```
(SOURCE_PRIORITY.index(source), source_seq)
```

### 9.3 Prohibiciones

No se aplica dedupe por:

- Titulo o titulo similar.
- Contenido o contenido similar.
- Embeddings.
- Umbrales de similitud.

---

## 10. Ranking BM25

### 10.1 Implementacion

Implementacion propia. No se usa libreria externa para BM25.

### 10.2 Corpus

Rankea sobre todos los `deduped_items` (no sobre items ya seleccionados).

### 10.3 doc_text

Para cada item:

```
doc_text = title + " " + content
```

### 10.4 Preprocessing congelado

Se aplica el mismo preprocessing a `doc_text` y a `query`:

1. Convertir a lowercase.
2. Eliminar puntuacion con regex fija.
3. Split por espacios.
4. Eliminar stopwords (lista fija congelada definida por el proyecto).
5. Sin stemming.
6. Sin lematizacion.

BM25 opera sobre los tokens resultantes.

### 10.5 Parametros BM25 congelados

| Parametro | Valor |
|-----------|-------|
| `k1`      | 1.5   |
| `b`       | 0.75  |

### 10.6 Orden total determinista congelado

Ordenar por:

```
(-bm25_score, title ASC, link ASC)
```

Tras ordenar, asignar `rank_position` (1..N) a cada item.

### 10.7 Output

`ranked_items`: lista ordenada donde cada item incluye `bm25_score` y `rank_position`.

---

## 11. Select

### 11.1 Parametros de top_k

| Propiedad  | Valor |
|------------|-------|
| Rango      | [1..5] |
| Default    | 3     |

### 11.2 Regla de seleccion

```
effective_k = min(top_k, len(ranked_items))
selected_items = ranked_items[:effective_k]
```

No se aborta si `len(ranked_items) < top_k`.

---

## 12. Summarize (map-reduce secuencial tolerante)

### 12.1 summarize_map

Ejecucion secuencial (no paralela) sobre cada `selected_item`.

Subgrafo por item:

1. `summarize_one`: invoca LLM para generar el campo `summary`.
2. `validate_summary_schema`: valida limites y formato por item.

Si un item falla (error de LLM o violacion de schema):

- No se incluye en `results`.
- Se incrementa el contador `failed` en `summary_stats`.
- No se aborta el pipeline en este punto.

`summary_stats` contiene:

- `ok` (int): summaries generados correctamente.
- `failed` (int): summaries que fallaron.

### 12.2 summarize_reduce

1. Filtra solo summaries validos.
2. Reordena resultados por `rank_position`.
3. Construye `results` y el output publico final.
4. Si `len(results) == 0` -> abort `SUMMARY_ALL_ITEMS_FAILED`.
5. No usa LLM.

---

## 13. Output publico v2

### 13.1 Estructura de output

```json
{
  "topic": "string",
  "time_window": "string",
  "requested_k": "int",
  "returned_k": "int",
  "failed_summaries": "int",
  "results": [
    {
      "title": "string",
      "summary": "string",
      "link": "string",
      "source": "string",
      "rank_position": "int"
    }
  ]
}
```

### 13.2 Trazabilidad

Cada resultado incluye:

- `source`: fuente de origen del paper.
- `rank_position`: posicion en el ranking BM25 (1..N).

### 13.3 Exclusiones

No se incluye insight transversal en v2.

---

## 14. State cerrado

### 14.1 Politica

Lista cerrada de claves permitidas. No se admiten claves fuera de esta lista.

### 14.2 Claves de input publico

- `query`
- `time_window`
- `top_k` (opcional)

### 14.3 Claves de state interno

| Clave                  | Descripcion                                              |
|------------------------|----------------------------------------------------------|
| `input_raw`            | Input crudo del usuario                                  |
| `input_validated`      | Input validado con defaults aplicados                    |
| `source_units`         | Unidades crudas por fuente (`status`, `error`, `items` por fuente) |
| `merged_source_units`  | Unidades concatenadas y ordenadas deterministamente      |
| `normalized_items`     | Items normalizados con schema comun                      |
| `filtered_items`       | Items tras filtro temporal                               |
| `deduped_items`        | Items tras deduplicacion por `canonical_id`              |
| `ranked_items`         | Items ordenados por BM25 con `rank_position`             |
| `selected_items`       | Items seleccionados (top_k)                              |
| `summary_items`        | Summaries validos con trazabilidad (`rank_position`, `title`, `summary`, `link`, `source`) |
| `summary_stats`        | Contadores de summarize: `ok` y `failed`                 |
| `output`               | Output publico final                                     |
| `abort_reason`         | Codigo de abort (si aplica)                              |

### 14.4 Reglas operativas

- No hay mutacion in-place de state en nodos.
- Cada nodo retorna solo su delta (`dict` parcial).
- LangGraph realiza el merge de estado.
- `output` y `abort_reason` no coexisten en una ejecucion abortada.

---

## 15. Codigos de abort v2

| Codigo                          | Origen                  | Condicion                                       |
|---------------------------------|-------------------------|-------------------------------------------------|
| `EMPTY_INPUT_PAYLOAD`           | `collect_input`         | Input vacio o ausente                           |
| `INVALID_QUERY`                 | `validate_input`        | Query no cumple formato                         |
| `INVALID_TIME_WINDOW`           | `validate_input`        | Ventana temporal no reconocida                  |
| `INVALID_TOP_K`                 | `validate_input`        | top_k fuera de rango [1..5]                     |
| `FETCH_ALL_SOURCES_FAILED`      | `merge_source_units`    | Todas las fuentes fallaron                      |
| `UNKNOWN_SOURCE_PRIORITY`       | `merge_source_units`    | `source_units` contiene clave no incluida en `SOURCE_PRIORITY` |
| `NO_ITEMS_IN_TIME_WINDOW`       | `filter_by_time_window` | Sin items tras filtro temporal                  |
| `RANK_QUERY_EMPTY_AFTER_NORMALIZATION` | `rank_bm25`     | Query vacia tras preprocessing                  |
| `SELECT_MISSING_RANKED_ITEMS`   | `select`                | `ranked_items` ausente o invalido               |
| `SELECT_TOPK_INVALID`           | `select`                | `top_k` invalido en runtime                     |
| `NO_ITEMS_AFTER_DEDUPE`         | `dedupe`                | Sin items tras deduplicacion                    |
| `SUMMARY_ALL_ITEMS_FAILED`      | `summarize_reduce`      | Todos los summaries fallaron                    |

---

## 16. Invariantes v2

1. **Determinismo estructural**: mismo input + mismo snapshot de fuentes -> mismo conjunto y orden hasta `rank_bm25`. Solo la redaccion del LLM puede variar.
2. **Separacion de responsabilidades estricta**: cada nodo tiene una unica responsabilidad definida.
3. **Dedupe solo estructural**: por `canonical_id`, sin semantica.
4. **Ranking puramente textual**: BM25 con parametros congelados, sin senales externas.
5. **Politica de fallo definida y estable**: degradacion controlada en fetch y summarize, abort solo si fallo total.
6. **results <= top_k**: no se exige igualdad, se garantiza cota superior.

---

## 17. Relacion con versiones anteriores

| Version | Estado  | Runtime                      | Ubicacion                        |
|---------|---------|------------------------------|----------------------------------|
| v2      | FROZEN  | LangGraph (`graph.invoke()`) | Branch de desarrollo             |
| v1.1    | FROZEN  | LangGraph (`graph.invoke()`) | Tag `v1.1.0`, branch `v1.1`     |
| v1      | FROZEN  | Loop manual                  | Tag `v1.0.0`, branch `codex/legacy-v1` |
