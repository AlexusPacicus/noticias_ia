# noticias — v1.1

Busca papers recientes de IA en arXiv, los rankea por relevancia contra tu query y genera resumenes cortos con un LLM local.

---

## Como funciona

Le das una query (ej. `"large language models"`), una ventana temporal y cuantos resultados quieres. El sistema:

1. Busca en arXiv `cs.AI` dentro de esa ventana.
2. Rankea los papers por coincidencia lexica con tu query (determinista, sin ML).
3. Selecciona los top-k.
4. Genera un resumen breve de cada uno con `gemma3:4b` via Ollama.

El ranking y la seleccion son siempre los mismos para el mismo input. Lo unico que varia entre ejecuciones es la redaccion de los resumenes.

---

## Pipeline

```
collect_input -> validate_input -> fetch -> normalize -> rank -> select -> summarize
```

| Paso             | Que hace                                                      |
|------------------|---------------------------------------------------------------|
| `collect_input`  | Recoge lo que el usuario paso.                                |
| `validate_input` | Verifica formato y aplica defaults.                           |
| `fetch`          | Trae papers de arXiv filtrados por fecha.                     |
| `normalize`      | Extrae `title`, `link` y `content` de cada paper.            |
| `rank`           | Ordena por coincidencia de palabras con la query.             |
| `select`         | Se queda con los primeros `top_k`.                            |
| `summarize`      | Pide al LLM un resumen breve de cada paper seleccionado.      |

Si algo falla en cualquier paso, el pipeline se detiene y devuelve el motivo del error. No hay resultados parciales.

El runtime es LangGraph: todo se ejecuta via `graph.invoke(input)`.

---

## Entrada y salida

**Entrada:**

| Campo         | Tipo   | Notas                                         |
|---------------|--------|-----------------------------------------------|
| `query`       | string | Min. 2 palabras. Sin `AND`/`OR`/`NOT`.        |
| `time_window` | string | `last_24h`, `last_3_days` o `last_7_days`.    |
| `top_k`       | int    | Opcional. Entre 1 y 10, default 5.            |

**Salida (exito):**

```json
{
  "output": {
    "topic": "large language models",
    "time_window": "last_7_days",
    "results": [
      {
        "title": "Nombre del paper",
        "idea_clave": "De que trata (max 80 palabras)",
        "relacion_con_query": "Por que es relevante (max 30 palabras)",
        "link": "http://arxiv.org/abs/..."
      }
    ]
  }
}
```

**Salida (error):**

```json
{
  "abort_reason": "INVALID_QUERY"
}
```

Todos los codigos de error estan listados en `docs/v1.1/Contrato_Sistema_v1.1.md`.

---

## Ejecutar

Necesitas Python 3.11+ y [Ollama](https://ollama.com/) con el modelo `gemma3:4b` descargado.

```bash
pip install -r requirements.txt
python run_pipeline.py
```

---

## Tests

```bash
# Unitarios (sin red, sin LLM)
pytest -q -m "not integration and not e2e"

# Integracion (necesita arXiv)
pytest -q -m integration

# End-to-end (necesita arXiv + Ollama)
pytest -q -m e2e
```

30 tests unitarios.

---

## Limitaciones conocidas

El modelo `gemma3:4b` es pequeno y no siempre respeta los limites de palabras del schema. Cuantos mas papers procesa (top_k alto), mas probable es que alguno falle validacion. En pruebas con `top_k=3` la tasa de fallo rondo el 75%.

Cuando esto pasa, el pipeline detecta la violacion y aborta limpiamente. No es un bug del sistema sino una limitacion del modelo. Un modelo mas grande o un limite de tokens mas generoso lo resolveria sin tocar el pipeline.

---

## Versiones

| Version | Estado | Que usa                      | Donde esta                             |
|---------|--------|------------------------------|----------------------------------------|
| v1.1    | FROZEN | LangGraph (`graph.invoke()`) | Tag `v1.1.0`, branch `v1.1`           |
| v1      | FROZEN | Loop manual                  | Tag `v1.0.0`, branch `codex/legacy-v1` |

This branch exclusively maintains v2 architecture. v1 is available in historical tag.

---

## Documentacion

Contratos y especificaciones detalladas:

- [`Contrato_Sistema_v1.1.md`](docs/v1.1/Contrato_Sistema_v1.1.md)
- [`Contrato_Runtime_v1.1.md`](docs/v1.1/Contrato_Runtime_v1.1.md)
- [`Contrato_State_v1.1.md`](docs/v1.1/Contrato_State_v1.1.md)
- [`CHANGELOG_v1.1.md`](CHANGELOG_v1.1.md) — que cambio de v1 a v1.1.
- [`docs/legacy/v1/`](docs/legacy/v1/) — documentacion historica de v1.
