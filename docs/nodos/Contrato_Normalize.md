# Contrato de Nodo — `normalize`

---

## 1. Propósito

Mapear `external_units` a una colección `normalized_items` conforme a un schema mínimo cerrado.

**No** se permite aplicar criterio, filtrado, deduplicación, ranking, interpretación semántica ni enriquecimiento.

---

## 2. Lecturas permitidas (State)

- `external_units` (obligatorio).

**Lecturas prohibidas:**

- Cualquier otro campo del State.
- Cualquier estado interno de nodos previos.
- Artefactos exógenos, configuración, red o filesystem.

---

## 3. Escrituras permitidas

**Campo creado:** `normalized_items`

Colección iterable donde cada ítem cumple el siguiente schema mínimo cerrado:

```json
{
  "title": "string",
  "link": "string",
  "content": "string"
}
```

- `title`: valor textual literal de la unidad externa.
- `link`: identificador literal de la unidad externa. Se considera identificador único por unidad.
- `content`: contenido textual de la unidad externa.

**Mapeo v1 (arXiv `cs.AI`):**

| Campo schema | Campo arXiv        |
|--------------|--------------------|
| `title`      | elemento `title`   |
| `link`       | elemento `id`      |
| `content`    | elemento `summary` |

Este mapeo es mecánico y literal. No introduce criterio, interpretación ni transformación del contenido. Es específico de v1; cambiar de fuente implica nueva versión contractual.

**Reglas:**

- Se crea una única vez, de modo atómico: si no puede formarse conforme a schema, no se escribe y la ejecución aborta.
- El orden se mantiene tal cual el de `external_units`.
- Cada ítem corresponde 1:1 a una unidad externa.
- No se permiten campos adicionales.
- Una vez creado, no puede ser modificado por nodos posteriores.

---

## 4. Invariantes locales

- El nodo **no modifica** ni filtra `external_units`.
- No interpreta ni enriquece el contenido.
- Cada ítem nuevo corresponde 1:1 a una unidad externa.
- Si no se aborta, **todas** las unidades están en `normalized_items` y cumplen el schema.
- Si el nodo completa su ejecución, `normalized_items` existe obligatoriamente en el State.
- Si `external_units` es una colección vacía, `normalized_items` se crea como colección vacía. No es abort.

---

## 5. Aborts específicos

### `NORMALIZE_MISSING_TITLE`

- `title` ausente, no es string, o vacío.

### `NORMALIZE_MISSING_LINK`

- `link` ausente, no es string, o vacío.

### `NORMALIZE_MISSING_CONTENT`

- `content` ausente, no es string, o vacío tras limpieza.

**Regla contractual:**
Ante cualquier abort:

- No se escribe `normalized_items`.
- El nodo señaliza abort lanzando excepción. El runtime escribe `abort_reason`.
- El pipeline se detiene.

**Mapeo contractual:**
↳ Abort general 4 — Imposibilidad de validación ex-post.

---

## 6. Prohibiciones explícitas

Queda prohibido a este nodo:

- Leer cualquier campo del State distinto de `external_units`.
- Enriquecer, resumir o interpretar contenido.
- Clasificar con LLM o cualquier heurística.
- Eliminar elementos de la colección.
- Añadir campos no definidos en el schema.
- Deduplicar ítems.
- Parsear o extraer fechas.
- Acceder a red, filesystem o artefactos exógenos.

**Regla dura:**
Cualquier violación activa **Abort 5 — Ambigüedad de responsabilidad**.

---

## 7. Notas de gobernanza

Nodo exclusivamente estructural, sin criterio ni validación de contenido.

- Marca el límite entre datos externos sin garantía de forma y datos internos con forma mínima gobernada.
- Cualquier ampliación del schema (nuevos campos, deduplicación, fechas) implica **nueva versión contractual**.

---

## 8. Estado del contrato

- **Versión:** v1
- **Estado:** **FROZEN**
