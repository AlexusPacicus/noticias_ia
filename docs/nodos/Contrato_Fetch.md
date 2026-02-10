# Contrato de Nodo — `fetch`

---

## 1. Propósito

Transferir al State la respuesta literal de la fuente autorizada, sin aplicar criterio, filtrado, normalización, interpretación ni enriquecimiento.

---

## 2. Lecturas permitidas (State)

- `input_validated` (obligatorio).

**Lecturas prohibidas:**

- Cualquier otro campo del State.
- Cualquier estado interno de nodos previos.
- Artefactos exógenos a través de cualquier mecanismo distinto del contrato de sistema.

---

## 3. Escrituras permitidas

**Campo creado:** `external_units`

`external_units` colección iterable de unidades externas trasladadas literalmente.

**Reglas contractuales:**

- Se crea una única vez en este nodo.
- No puede ser modificada por nodos posteriores.
- No existe ninguna garantía contractual sobre el orden de las unidades externas.
- No se aplica:
  - ranking,
  - filtrado,
  - deduplicación,
  - normalización,
  - interpretación semántica.

“Cualquier decisión sobre validez interna, orden o significado de las unidades externas pertenece exclusivamente a nodos posteriores del pipeline.

---

## 4. Invariantes locales

- Si el nodo completa su ejecución, el campo `external_units` existe obligatoriamente en el State.
- `fetch` no introduce criterio ni toma decisiones sobre las unidades externas obtenidas.
- `fetch` no modifica el contenido recibido de la fuente autorizada.
- `fetch` no persiste estado entre ejecuciones.

Estos invariantes deben cumplirse en toda ejecución válida del nodo.

---

## 5. Relación con artefactos exógenos

- `fetch` opera exclusivamente sobre las fuentes definidas como artefactos exógenos del sistema v1.
- `fetch` no selecciona, prioriza ni rota fuentes.
- `fetch` no implementa mecanismos de fallback ni alternativas ante fallo de una fuente.
- `fetch` no puede modificar endpoints, categorías ni parámetros definidos fuera del runtime.

Cualquier cambio en las fuentes, sus endpoints o su configuración constituye un cambio de sistema y requiere **nueva versión**.

---

## 6. Aborts específicos

`fetch` puede abortar la ejecución únicamente cuando no es posible trasladar datos externos al sistema gobernado de forma válida.

### `FETCH_SOURCE_ERROR`

La fuente no responde, responde con error técnico, **o devuelve explícitamente un error de la propia fuente aunque el payload sea legible**.
No es posible garantizar la transferencia literal de datos externos.

### `FETCH_NOT_ITERABLE`

No se puede obtener una colección iterable sin interpretación.

### `FETCH_EMPTY_RESPONSE`

La fuente responde correctamente pero no devuelve ninguna unidad externa. En v1 se declara contractualmente que avanzar sin estas no es válido.
Esta es una decisión específica del sistema v1, no una propiedad general del nodo fetch.

**Regla contractual:**
Ante cualquier abort:

- No se escribe `external_units`.
- Se escribe `abort_reason`.
- El pipeline se detiene.

**Mapeo contractual:**
Todos los aborts específicos de este nodo mapean a ↳ Abort general 4 — Imposibilidad de validación ex-post.

---

## 7. Prohibiciones explícitas

- Prohibido leer cualquier campo del State distinto de `input_validated`.
- Prohibido escribir cualquier campo distinto de `external_units`.
- Prohibido filtrar, ordenar, deduplicar o transformar unidades externas.
- Prohibido inferir validez, relevancia o significado.
- Prohibido aplicar heurísticas, defaults o correcciones.
- Prohibido seleccionar, rotar o hacer fallback de fuentes.
- Prohibido introducir metadatos de ejecución o estado interno.
- Prohibido persistir estado entre ejecuciones.

**Regla dura:**
Cualquier violación activa **Abort 5 — Ambigüedad de responsabilidad**.

---

## 8. Notas de gobernanza

`fetch` es un nodo de frontera externa.

- Todo comportamiento no gobernado por contrato se contiene aquí y no se propaga al resto del pipeline.
- Este nodo no garantiza determinismo inter-ejecución, pero sí garantiza aislamiento, trazabilidad y ausencia de criterio.

A partir de este punto, todos los datos se consideran dentro del sistema gobernado y solo pueden ser tratados conforme a los contratos posteriores.
