# Diseño del sistema de selección y resumen de ítems IA

## Propósito

El sistema, dado un `query` y un `time_window`, selecciona y resume ítems recientes (papers, noticias, releases) del ámbito de la IA de manera descriptiva y priorizada, sin incorporar juicio experto.

- **Consulta fuentes cerradas**.
- **Prioriza resultados con un scoring determinista**.
- **Selecciona los top-K ítems**.
- **Genera resúmenes breves y estructurados**.
- **Devuelve un resultado estable y reproducible** (el resumen puede cambiar levemente, pero el conjunto y orden de los ítems no).

## Qué hace y qué no hace

**Hace:**
- Consulta fuentes cerradas y predefinidas.
- Escoge solo los más relevantes según un ranking objetivo.
- Responde con resúmenes estructurados, directos y descriptivos.

**No hace:**
- No cubre exhaustivamente un tema.
- No detecta tendencias ni predice impacto futuro.
- No compara ni evalúa la calidad científica de los ítems.
- No personaliza respuestas ni aprende del histórico.
- No utiliza embeddings, RAG ni mantiene estado persistente.

## Reglas principales

- **El modelo LLM únicamente transforma texto.**
- **El LLM no participa del ranking ni de la selección final.**
- **Ningún nodo añade semántica fuera del contrato definido.**

---

## Contrato I/O v0 (FROZEN)

### Input

- `query`: cadena de texto (mínimo 2 palabras, sin operadores ni filtros avanzados).
- `time_window`: uno de los siguientes valores:
  - `last_24h`
  - `last_3_days`
  - `last_7_days`
  - `last_30_days`
- `top_k`: número (opcional, entre 1 y 10, por defecto 5).

### Output

```yaml
{
  topic: string,
  time_window: string,
  generated_at: datetime,
  results: [
    {
      kind: paper | news | release,
      title: string,
      idea_clave: string,  // hasta 60 palabras, qué es
      por_que_importa: string, // hasta 40 palabras, contexto factual
      link: string // único
    },
    ...
  ]
}
```

- Un máximo de K resultados, ordenados por prioridad.
- `kind` es un enum cerrado.
- Cada resumen es estrictamente descriptivo (sin opiniones, comparaciones, hype ni predicciones).
- Un único enlace canónico por ítem.

### Errores posibles

- `INVALID_QUERY`
- `INVALID_TIME_WINDOW`
- `INVALID_TOP_K`
- `EMPTY_RESULTS`
- `INVALID_KIND`
- `SUMMARY_SCHEMA_VIOLATION`

Cualquier violación termina la ejecución con error (sin resultado parcial).

---

## Fuentes permitidas (v0)

- **arXiv**: cs.AI y cs.CL (papers)
- **Blogs oficiales**: OpenAI, Google, Anthropic (releases)
- **Medios especializados**: restringidos (news)
- *No se permiten newsletters, redes sociales, agregadores, blogs personales, foros, etc.*

Las fuentes son fijas y declarar nuevas implica un cambio de versión.

---

## Pipeline (v0, FROZEN)

1. **collect_input**: ingesta y parsing del input de usuario.
2. **validate_input**: valida contrato y aplica defaults.
3. **fetch**: consulta fuentes permitidas.
4. **normalize**: unifica y deduplica ítems.
5. **rank**: aplica scoring determinista (sin LLM ni subjetividad).
6. **select**: selecciona top_k según ranking.
7. **summarize**: Resume los ítems (único paso usando LLM).

**Reglas:**
- Cada módulo tiene una sola responsabilidad.
- Validar antes de hacer llamadas externas.
- El input nunca salta pasos del pipeline.

---

## Tests mínimos de estabilidad

- Objetivo: verificar estabilidad y determinismo del pipeline con queries de ejemplo en papers y releases.
- Configuración: `time_window = last_7_days, top_k = 5`
- Se ejecutan dos veces idénticas cada query.
- Se comprueba:
  - Orden idéntico entre ejecuciones.
  - El mismo conjunto de resultados.
  - Cumplimiento estricto del schema.
  - Variación solo en la redacción, no en contenido o estructura.
- **Si alguna prueba falla, se detiene el avance de versión.**
