# noticias -- v1.1

Sistema gobernado por contrato para seleccion y resumen de items recientes sobre IA a partir de fuentes reales y cerradas. Runtime oficial sobre LangGraph.

---

## Overview

Dado un `query`, un `time_window` y un `top_k` opcional, el sistema obtiene items recientes de arXiv (`cs.AI`), los ordena por coincidencia lexica determinista y genera resumenes descriptivos mediante LLM.

El pipeline es fijo, determinista en seleccion y orden, y falla de forma explicita ante cualquier violacion contractual. El LLM opera unicamente como transformador de texto en el nodo final; no participa en ranking, seleccion ni filtrado.

---

## Architecture

Pipeline de orden fijo e inmutable, ejecutado como `StateGraph` compilado de LangGraph:

```
collect_input -> validate_input -> fetch -> normalize -> rank -> select -> summarize
```

| Nodo             | Responsabilidad                                                |
|------------------|----------------------------------------------------------------|
| `collect_input`  | Ingesta del input bruto del usuario.                           |
| `validate_input` | Validacion del contrato de entrada y aplicacion de defaults.   |
| `fetch`          | Obtencion de items desde arXiv, filtrados por ventana temporal.|
| `normalize`      | Mapeo a schema interno cerrado (`title`, `link`, `content`).  |
| `rank`           | Ordenacion lexica determinista por coincidencia con el query.  |
| `select`         | Seleccion de los primeros `top_k` items del ranking.           |
| `summarize`      | Generacion de resumenes descriptivos via LLM (1 por item).    |

**Runtime oficial:** `graph.invoke(input)` sobre el grafo compilado en `graph/graph.py:graph`.

Cada nodo retorna un dict parcial. LangGraph gestiona el merge de estado. Los nodos senalizan abort retornando `{"abort_reason": "CODIGO"}`; el router condicional redirige a `END`. No hay resultados parciales.

Detalle completo en los contratos de referencia (ver [Documentation](#documentation)).

---

## Public I/O Contract

**Input** (`InputState`, definido en `graph/state.py`):

| Campo         | Tipo             | Restriccion                                   |
|---------------|------------------|-----------------------------------------------|
| `query`       | `str`            | Min. 2 palabras, sin operadores booleanos.    |
| `time_window` | `str` (enum)     | `last_24h` \| `last_3_days` \| `last_7_days` |
| `top_k`       | `int` (opcional) | Rango `[1..10]`, default `5`.                 |

**Output** (`OutputState`, definido en `graph/state.py`):

- Ejecucion exitosa: `{"output": {...}}`
- Ejecucion abortada: `{"abort_reason": "CODIGO"}`

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

`output` y `abort_reason` no coexisten. Codigos de abort documentados en `docs/v1.1/Contrato_Sistema_v1.1.md`.

---

## Running Locally

**Requisitos:** Python 3.11+, [Ollama](https://ollama.com/) con modelo `gemma3:4b` disponible.

```bash
pip install -r requirements.txt
python run_pipeline.py
```

`run_pipeline.py` es un entrypoint de conveniencia que delega en `graph.invoke(...)`.

---

## Tests

```bash
# Unitarios (sin red ni LLM)
pytest -q -m "not integration and not e2e"

# Integracion (requiere arXiv)
pytest -q -m integration

# End-to-end (requiere arXiv + Ollama)
pytest -q -m e2e
```

30 tests unitarios. Markers definidos en `pytest.ini`.

---

## Versioning

| Version | Estado   | Runtime                  | Referencia                          |
|---------|----------|--------------------------|-------------------------------------|
| v1.1    | ACTIVE   | `graph.invoke()` (LangGraph) | Branch `v1.1`, docs activos    |
| v1      | FROZEN   | Loop manual (legacy)     | Tag `v1.0.0`, branch `codex/legacy-v1` |

v1 no se modifica. Cualquier cambio estructural sobre v1.1 implica nueva version.

Para ejecutar el runtime historico de v1:

```bash
git checkout v1.0.0
```

---

## Documentation

**Activa (v1.1):**

- [`docs/v1.1/Contrato_Sistema_v1.1.md`](docs/v1.1/Contrato_Sistema_v1.1.md)
- [`docs/v1.1/Contrato_Runtime_v1.1.md`](docs/v1.1/Contrato_Runtime_v1.1.md)
- [`docs/v1.1/Contrato_State_v1.1.md`](docs/v1.1/Contrato_State_v1.1.md)
- [`CHANGELOG_v1.1.md`](CHANGELOG_v1.1.md) -- cambios detallados v1 a v1.1.

**Legacy (v1, solo referencia historica):**

- [`docs/legacy/v1/`](docs/legacy/v1/) -- contratos congelados de sistema, state y nodos.
