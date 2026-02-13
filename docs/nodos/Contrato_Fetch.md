# Contrato de Nodo — `fetch`

---

## 1. Propósito

Transferir al State la respuesta de la fuente autorizada, parametrizada por `query` y `time_window`, sin aplicar criterio, normalización, interpretación ni enriquecimiento.

---

## 2. Lecturas permitidas (State)

- `input_validated` (obligatorio; acceso a `query` y `time_window`).

**Lecturas prohibidas:**

- Cualquier otro campo del State.
- Cualquier estado interno de nodos previos.
- Artefactos exógenos a través de cualquier mecanismo distinto del contrato de sistema.

---

## 3. Escrituras permitidas

**Campo creado:** `external_units`

Colección iterable de unidades externas obtenidas de la fuente.

**Parametrización:**

- La consulta a la fuente se parametriza usando `query` y `time_window` de `input_validated`.
- `query` se utiliza como término de búsqueda contra la fuente.
- `time_window` se utiliza para acotar temporalmente la consulta.
- Si la fuente no permite filtro temporal exacto, se aplica un filtro posterior determinista sobre la respuesta.

**Interpretación de `time_window` (v1):**

- `last_24h`: últimas 24 horas desde el momento de ejecución.
- `last_3_days`: últimos 3 días naturales.
- `last_7_days`: últimos 7 días naturales.
- La fecha de referencia de cada unidad es la fecha de publicación declarada por la fuente (arXiv: `published`).
- Zona horaria: UTC.
- Bordes: inclusivos (una unidad publicada exactamente en el límite se incluye).
- Solo se incluyen unidades cuya fecha de referencia cae dentro de la ventana.
- Si la fuente no expone fecha de publicación para una unidad, dicha unidad se excluye.
- Este filtro temporal es mecánico y determinista; no constituye filtrado semántico ni introduce criterio.

**Reglas contractuales:**

- Se crea una única vez en este nodo.
- No puede ser modificada por nodos posteriores.
- No existe ninguna garantía contractual sobre el orden de las unidades externas.
- No se aplica:
  - ranking,
  - deduplicación,
  - normalización,
  - interpretación semántica,
  - filtrado por contenido, relevancia o calidad.

Cualquier decisión sobre validez interna, orden o significado de las unidades externas pertenece exclusivamente a nodos posteriores del pipeline.

---

## 4. Invariantes locales

- Si el nodo completa su ejecución, el campo `external_units` existe obligatoriamente en el State.
- `fetch` no introduce criterio ni toma decisiones sobre las unidades externas obtenidas.
- `fetch` no modifica el contenido recibido de la fuente autorizada (salvo el filtro temporal declarado).
- `fetch` no persiste estado entre ejecuciones.

Estos invariantes deben cumplirse en toda ejecución válida del nodo.

---

## 5. Aborts específicos

### `FETCH_SOURCE_ERROR`

La fuente no responde, responde con error técnico, **o devuelve explícitamente un error de la propia fuente aunque el payload sea legible**.
No es posible garantizar la transferencia literal de datos externos.

### `FETCH_NOT_ITERABLE`

No se puede obtener una colección iterable sin interpretación.

**Regla contractual:**
Ante cualquier abort:

- No se escribe `external_units`.
- El nodo señaliza abort lanzando excepción. El runtime escribe `abort_reason`.
- El pipeline se detiene.

**Mapeo contractual:**
↳ Abort general 4 — Imposibilidad de validación ex-post.

---

## 6. Prohibiciones explícitas

Queda prohibido a este nodo:

- Leer cualquier campo del State distinto de `input_validated`.
- Escribir cualquier campo distinto de `external_units`.
- Filtrar por contenido, relevancia, calidad o significado.
- Ordenar, deduplicar o transformar unidades externas.
- Inferir validez, relevancia o significado.
- Aplicar heurísticas, defaults o correcciones.
- Seleccionar, rotar o hacer fallback de fuentes.
- Introducir metadatos de ejecución o estado interno.
- Persistir estado entre ejecuciones.

**Regla dura:**
Cualquier violación activa **Abort 5 — Ambigüedad de responsabilidad**.

---

## 7. Notas de gobernanza

`fetch` es un nodo de frontera externa.

- Todo comportamiento no gobernado por contrato se contiene aquí y no se propaga al resto del pipeline.
- Este nodo no garantiza determinismo inter-ejecución, pero sí garantiza aislamiento, trazabilidad y ausencia de criterio.
- `fetch` opera exclusivamente sobre las fuentes definidas como artefactos exógenos del sistema v1.
- No selecciona, prioriza ni rota fuentes.
- No implementa mecanismos de fallback ni alternativas ante fallo de una fuente.
- No puede modificar endpoints, categorías ni parámetros definidos fuera del runtime.

Cualquier cambio en las fuentes, sus endpoints o su configuración constituye un cambio de sistema y requiere **nueva versión**.

A partir de este punto, todos los datos se consideran dentro del sistema gobernado y solo pueden ser tratados conforme a los contratos posteriores.

---

## 8. Estado del contrato

- **Versión:** v1
- **Estado:** **FROZEN**
