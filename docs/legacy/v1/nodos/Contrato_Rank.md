# Contrato de Nodo — `rank`

---

## 1. Propósito

Ordenar `normalized_items` de forma determinista según coincidencia léxica exacta entre `query` y el contenido del ítem.

Sin inferencia. Sin LLM. Sin semántica adicional.

---

## 2. Lecturas permitidas (State)

- `normalized_items` (obligatorio).
- `input_validated` (acceso a `query`).

**Lecturas prohibidas:**

- Cualquier otro campo del State.
- Artefactos exógenos, configuración, red o filesystem.

---

## 3. Escrituras permitidas

**Campo creado:** `ranked_items`

Lista completa de `normalized_items` ordenada según el score contractual y los criterios de desempate.

**Reglas:**

- Se crea una única vez en este nodo.
- No puede ser modificado por nodos posteriores.
- La cardinalidad de `ranked_items` es idéntica a `normalized_items`.

---

## 4. Invariantes locales

### 4.1 Normalización textual contractual

Para cualquier texto `x`:

```
tokens(x):
  1. Convertir a lowercase.
  2. Reemplazar cualquier carácter no [a-z0-9] por espacio.
  3. Split por espacios.
  4. Eliminar tokens vacíos.
  5. Resultado: set (tokens únicos).
```

Definiciones:

- `Q = tokens(query)`
- `T = tokens(title + " " + content)`

### 4.2 Definición formal del score

```
score(item) = | Q ∩ T |
```

- Coincidencia por palabra exacta.
- Cada token cuenta máximo una vez.
- Sin frecuencia.
- Sin substring.
- Sin stemming.
- Sin fuzzy.
- Sin stopwords.
- Sin heurísticas.

### 4.3 Orden total determinista

```
1. score DESC
2. title ASC
3. link ASC
```

Este orden es total: no existen empates irresolubles.

### 4.4 Restricciones estructurales

- No se eliminan elementos.
- No se agregan elementos.
- No se modifican campos internos.
- No se añade el score al State.
- Si termina sin abortar, `ranked_items` existe obligatoriamente.
- Si `normalized_items` es una colección vacía, `ranked_items` se crea como colección vacía. No es abort.

---

## 5. Aborts específicos

### `RANK_QUERY_EMPTY_AFTER_NORMALIZATION`

- Tras aplicar la normalización textual contractual a `query`, el conjunto `Q` resulta vacío (`Q = ∅`).

**Regla contractual:**
Ante cualquier abort:

- No se escribe `ranked_items`.
- El nodo señaliza abort lanzando excepción. El runtime escribe `abort_reason`.
- El pipeline se detiene.

Los aborts son mutuamente excluyentes. El primer abort detectado detiene la ejecución.

**Mapeo contractual:**
↳ Abort general 4 — Imposibilidad de validación ex-post.

---

## 6. Prohibiciones explícitas

Queda prohibido a este nodo:

- Usar campos distintos de `title` y `content` para el cálculo del score.
- Introducir pesos manuales.
- Aplicar stemming, fuzzy, stopwords o embeddings.
- Reordenar fuera de la regla definida.
- Añadir score al State.
- Llamar a LLM.
- Crear campos auxiliares, temporales o derivados.

**Regla dura:**
Cualquier violación activa **Abort 5 — Ambigüedad de responsabilidad**.

---

## 7. Notas de gobernanza

Nodo determinista de priorización léxica mínima.

Cualquier cambio en:

- normalización textual,
- definición de token,
- fórmula del score,
- criterios de desempate,

implica **nueva versión contractual**.

---

## 8. Estado del contrato

- **Versión:** v1
- **Estado:** **FROZEN**
