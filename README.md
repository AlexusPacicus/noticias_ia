# noticias — v1.1

Seleccion y resumen de items recientes sobre IA desde fuentes reales y cerradas.
Pipeline gobernado por contrato. Runtime sobre LangGraph.

---

## Que hace

Recibe un `query`, un `time_window` y un `top_k` opcional.
Busca items recientes en arXiv (`cs.AI`), los ordena por coincidencia lexica determinista y genera resumenes descriptivos via LLM.

- La seleccion y el orden son deterministas. No hay heuristicas probabilisticas.
- El LLM solo interviene al final, como transformador de texto. No rankea, no filtra, no decide.
- Cualquier violacion contractual aborta la ejecucion de forma explicita.

---

## Arquitectura

Pipeline lineal, de orden fijo, ejecutado como `StateGraph` compilado de LangGraph:

```
collect_input -> validate_input -> fetch -> normalize -> rank -> select -> summarize
```

| Nodo             | Que hace                                                        |
|------------------|-----------------------------------------------------------------|
| `collect_input`  | Ingesta del input bruto del usuario.                            |
| `validate_input` | Valida contrato de entrada; aplica defaults.                    |
| `fetch`          | Obtiene items de arXiv, filtrados por ventana temporal.         |
| `normalize`      | Mapea a schema interno cerrado (`title`, `link`, `content`).   |
| `rank`           | Ordena por coincidencia lexica determinista contra el query.    |
| `select`         | Corta a los primeros `top_k` del ranking.                      |
| `summarize`      | Genera un resumen descriptivo por item via LLM.                |

**Invocacion:** `graph.invoke(input)` sobre el grafo compilado en `graph/graph.py:graph`.

Cada nodo retorna un dict parcial; LangGraph hace merge de estado.
Para abortar, un nodo retorna `{"abort_reason": "CODIGO"}` y un conditional edge redirige a `END`. No hay resultados parciales.

Contratos completos en [Documentation](#documentacion).

---

## Contrato de I/O

### Entrada

`InputState` (definido en `graph/state.py`):

| Campo         | Tipo             | Restriccion                                   |
|---------------|------------------|-----------------------------------------------|
| `query`       | `str`            | Min. 2 palabras, sin operadores booleanos.    |
| `time_window` | `str` (enum)     | `last_24h` \| `last_3_days` \| `last_7_days` |
| `top_k`       | `int` (opcional) | Rango `[1..10]`, default `5`.                 |

### Salida

`OutputState` (definido en `graph/state.py`):

- Exito: `{"output": {...}}`
- Abort: `{"abort_reason": "CODIGO"}`

Nunca coexisten. Codigos de abort en `docs/v1.1/Contrato_Sistema_v1.1.md`.

Schema de `output`:

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

---

## Ejecucion local

**Requisitos:** Python 3.11+, [Ollama](https://ollama.com/) con `gemma3:4b` disponible.

```bash
pip install -r requirements.txt
python run_pipeline.py
```

`run_pipeline.py` es un wrapper liviano que delega en `graph.invoke(...)`.

---

## Tests

```bash
# Unitarios — sin red, sin LLM
pytest -q -m "not integration and not e2e"

# Integracion — requiere arXiv
pytest -q -m integration

# End-to-end — requiere arXiv + Ollama
pytest -q -m e2e
```

30 tests unitarios. Markers en `pytest.ini`.

---

## Limitaciones conocidas

**Fragilidad del LLM con `top_k` alto.**
El modelo `gemma3:4b` (`num_predict=200`, `temperature=0.1`) no respeta de forma fiable los limites de schema (`idea_clave` max 80 palabras, `relacion_con_query` max 30 palabras) cuando procesa items con abstracts largos. La probabilidad de `SUMMARY_SCHEMA_VIOLATION` crece con `top_k`: a mayor numero de items, mas invocaciones al LLM y mas oportunidades de violacion. En pruebas de estres con `top_k=3`, la tasa de abort por schema fue de ~75%.

El pipeline se comporta correctamente ante esta situacion: detecta la violacion, aborta y no devuelve resultados parciales. La fragilidad no es del sistema de gobernanza sino de la capacidad del modelo. Un modelo mayor o un `num_predict` mas generoso reducirian la tasa de fallo sin cambios en el pipeline.

---

## Versionado

| Version | Estado | Runtime                      | Referencia                            |
|---------|--------|------------------------------|---------------------------------------|
| v1.1    | ACTIVE | `graph.invoke()` (LangGraph) | Branch `v1.1`, docs activos          |
| v1      | FROZEN | Loop manual (legacy)         | Tag `v1.0.0`, branch `codex/legacy-v1` |

v1 esta congelada. Cualquier cambio estructural sobre v1.1 implica version nueva.

```bash
# Para ejecutar el runtime historico de v1:
git checkout v1.0.0
```

---

## Documentacion

**v1.1 (activa):**

- [`Contrato_Sistema_v1.1.md`](docs/v1.1/Contrato_Sistema_v1.1.md) — contrato de sistema.
- [`Contrato_Runtime_v1.1.md`](docs/v1.1/Contrato_Runtime_v1.1.md) — contrato de runtime.
- [`Contrato_State_v1.1.md`](docs/v1.1/Contrato_State_v1.1.md) — contrato de state.
- [`CHANGELOG_v1.1.md`](CHANGELOG_v1.1.md) — cambios detallados de v1 a v1.1.

**v1 (legacy, solo referencia historica):**

- [`docs/legacy/v1/`](docs/legacy/v1/) — contratos congelados de sistema, state y nodos.
