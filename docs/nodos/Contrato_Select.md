# Contrato de Nodo — `select`

---

## 1. Propósito

Seleccionar los primeros `top_k` elementos de `ranked_items`, respetando estrictamente su orden contractual.

El nodo no introduce criterio nuevo. No recalcula score. No reordena. No filtra por relevancia.

---

## 2. Lecturas permitidas (State)

- `ranked_items` (obligatorio).
- `input_validated` (acceso a `top_k`).

**Lecturas prohibidas:**

- Cualquier otro campo del State.
- Artefactos exógenos, configuración, red o filesystem.

---

## 3. Escrituras permitidas

**Campo creado:** `selected_items`

**Regla contractual formal:**

Sea:

- `N = len(ranked_items)`
- `K = input_validated["top_k"]`

Entonces:

```
selected_items = ranked_items[0 : min(K, N)]
```

**Interpretación cerrada:**

- Si `K ≤ N` → se seleccionan exactamente `K` elementos.
- Si `K > N` → se seleccionan exactamente `N` elementos.
- Nunca se seleccionan más de `K`.
- Nunca se seleccionan elementos fuera del prefijo del ranking.
- Select devuelve hasta `top_k` elementos aunque todos tengan score 0. **No existe abort por irrelevancia.**

**Reglas:**

- Se crea una única vez en este nodo.
- No puede ser modificado por nodos posteriores.

---

## 4. Invariantes locales

- No se recalcula score.
- No se reordena la lista.
- No se aplican filtros adicionales.
- No se modifican campos internos.
- Se preserva el orden exacto de `ranked_items`.
- Cardinalidad: `0 ≤ len(selected_items) ≤ K`.
- Si termina sin abortar, `selected_items` existe obligatoriamente.
- Si `ranked_items` es una lista vacía, `selected_items` se crea como lista vacía. No es abort.

---

## 5. Aborts específicos

### `SELECT_MISSING_RANKED_ITEMS`

- `ranked_items` no existe o no es lista.

### `SELECT_TOPK_INVALID`

- `top_k` no es entero o `top_k ≤ 0`.

**Regla contractual:**
Ante cualquier abort:

- No se escribe `selected_items`.
- El nodo señaliza abort lanzando excepción. El runtime escribe `abort_reason`.
- El pipeline se detiene.

**Mapeo contractual:**
↳ Abort general 4 — Imposibilidad de validación ex-post.

---

## 6. Prohibiciones explícitas

Queda prohibido a este nodo:

- Reordenar antes de cortar.
- Aplicar filtros adicionales (por score, por relevancia, por contenido).
- Recalcular score.
- Usar cualquier campo distinto de `ranked_items` e `input_validated`.
- Llamar a LLM.
- Añadir métricas, flags o campos auxiliares.

**Regla dura:**
Cualquier violación activa **Abort 5 — Ambigüedad de responsabilidad**.

---

## 7. Notas de gobernanza

Nodo estrictamente mecánico.

Cualquier cambio en:

- política de selección,
- uso de umbral en lugar de `top_k`,
- filtrado por score mínimo,

implica **nueva versión contractual**.

---

## 8. Estado del contrato

- **Versión:** v1
- **Estado:** **FROZEN**
