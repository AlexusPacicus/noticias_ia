1. Propósito

Organizar external_units en una colección normalized_items conforme a un schema mínimo cerrado, sin aplicar criterio, filtrado, deduplicación, ranking, interpretación semántica ni enriquecimiento.

2. Lecturas 
2.1 permitidas (State)
- external_units (obligatorio).
 2.2 prohibidas:
- Cualquier otro campo del State.
- Cualquier estado interno de nodos previos.
- Artefactos exógenos

3. Escrituras permitidas
Campo creado: normalized_items
normalized_items es una colección iterable de ítems organizados conforme a un schema mínimo cerrado, a partir de external_units.
3.1 Schema mínimo (cerrado)
Cada ítem en normalized_items debe cumplir exactamente:
{
  "title": "string",
  "link": "string",
  "raw": "object"
}
title: valor textual literal presente en la unidad externa.
link: identificador literal presente en la unidad externa.
raw: payload original completo de la unidad externa, sin modificación.
3.2 Reglas contractuales de escritura
normalized_items se crea una única vez en este nodo.
La escritura es atómica:
o se escribe completa y válida,
o no se escribe y la ejecución aborta.
normalized_items se escribe únicamente si todas las unidades de external_units pueden organizarse conforme al schema mínimo mediante operaciones estructurales locales de este nodo.
El orden de normalized_items preserva el orden de iteración de external_units.
normalized_items no puede ser modificado por nodos posteriores.
No se añaden campos auxiliares, derivados ni metadatos introducidos por este nodo.

4. Invariantes locales
normalize_schema no modifica el contenido de external_units.
normalize_schema no descarta unidades externas.
normalize_schema no interpreta contenido ni semántica.
normalize_schema puede reorganizar estructuralmente cada unidad externa para ajustarla al schema mínimo, sin alterar su significado.
normalize_schema introduce únicamente metadatos estructurales requeridos por el schema mínimo.
Cada ítem de normalized_items:
corresponde 1:1 con una unidad de external_units,
preserva íntegramente el payload original en raw.
Si el nodo completa su ejecución sin abortar:
normalized_items existe obligatoriamente,
todos sus ítems cumplen el schema mínimo cerrado.

## 5. Aborts específicos

`normalize_schema` puede abortar únicamente cuando no es posible organizar las unidades externas conforme al schema mínimo.

### SCHEMA_UNIT_NOT_MAPPABLE
Existe al menos una unidad externa que no puede organizarse conforme al schema mínimo sin alterar su significado.

### SCHEMA_INVALID_TYPE
Algún campo requerido (`title` o `link`) existe pero su tipo no es compatible con el schema mínimo.

Regla contractual:
- No se escribe `normalized_items`.
- Se escribe `abort_reason`.
- El pipeline se detiene.

Mapeo contractual:
↳ Abort general 4 — Imposibilidad de validación ex-post.

6. Prohibiciones explícitas

Queda prohibido a normalize_schema:
Leer cualquier campo del State distinto de external_units.
Escribir cualquier campo distinto de normalized_items.
Modificar external_units o cualquier unidad externa.
Descartar, filtrar o deduplicar unidades externas.
Reordenar unidades externas más allá de la reorganización estructural requerida por el schema mínimo.
Introducir metadatos de ejecución propios del nodo (timestamps, contadores, flags, estados internos).
Acceder a artefactos exógenos, configuración runtime, red, filesystem, reloj o entorno.
Persistir estado entre ejecuciones.
Regla dura:
Cualquier violación activa Abort 5 — Ambigüedad de responsabilidad.

7. Notas de gobernanza
normalize_schema es un nodo de organización estructural.
Organiza datos externos heterogéneos en una estructura interna conforme a un schema mínimo cerrado.
No introduce criterio, interpretación ni validación de contenido.
No depende de la fuente ni de decisiones externas al propio contrato.
Cualquier decisión que exceda la organización estructural:
desplaza responsabilidad,
rompe el aislamiento contractual del nodo,
y activa Abort 5 — Ambigüedad de responsabilidad.
Este nodo define el límite estructural entre datos externos sin forma contractual y datos internos con forma mínima gobernada.
