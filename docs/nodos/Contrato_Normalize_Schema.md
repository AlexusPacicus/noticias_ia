# Contrato del Nodo: normalize_schema

## 1. Propósito

Organizar `external_units` en una colección llamada `normalized_items`, ajustada a un _schema mínimo cerrado_.  
**No** se permite aplicar criterio, filtrado, deduplicación, ranking, interpretación semántica ni enriquecimiento. El nodo es puramente estructural.

---

## 2. Lecturas permitidas

- **Permitido:** solo puede leer `external_units` del State.
- **Prohibido:** no puede leer ningún otro campo del State, estados internos previos, ni artefactos externos.

---

## 3. Escrituras permitidas

- **Campo creado:** `normalized_items`  
  Esta colección es **iterable** y cada ítem debe cumplir el siguiente **schema mínimo**:

```json
{
  "title": "string",
  "link": "string",
  "raw": "object"
}
```
- `title`: valor textual literal de la unidad externa
- `link`: identificador literal de la unidad externa
- `raw`: todo el payload original de la unidad externa (sin modificar)

**Reglas:**
- Solo se crea una vez, y de modo atómico: si no puede formarse conforme a schema, no se escribe y la ejecución aborta.
- El orden se mantiene tal cual el de `external_units`.
- Una vez creado, no puede ser modificado por otros nodos ni enriquecido con metadatos.

---

## 4. Invariantes locales

- El nodo **no modifica** ni filtra `external_units`.
- No interpreta ni enriquece el contenido.
- Cada ítem nuevo corresponde 1:1 a una unidad externa, preservando el payload original en `raw`.
- Si no se aborta, **todas** las unidades están en `normalized_items` y cumplen el schema.

---

## 5. Aborts específicos

El nodo puede abortar **únicamente** si alguna unidad externa:
- No puede organizarse al schema mínimo sin perder el significado (**SCHEMA_UNIT_NOT_MAPPABLE**)
- Tiene un campo requerido (`title`, `link`) cuyo tipo es incompatible (**SCHEMA_INVALID_TYPE**)

En caso de abortar:
- No se escribe `normalized_items`
- Se escribe `abort_reason`
- El pipeline se detiene

---

## 6. Prohibiciones explícitas

Prohibido, explícitamente:
- Leer cualquier campo del State salvo `external_units`
- Escribir campos distintos de `normalized_items`
- Modificar, filtrar, deduplicar o descartar `external_units`
- Reordenar salvo para el ajuste estructural al schema
- Introducir metadatos o estados internos
- Acceso externo (red, reloj, entorno, disco)
- Persistencia entre ejecuciones

*Cualquier violación aborta por Ambigüedad de responsabilidad.*

---

## 7. Gobernanza y límites

- Nodo exclusivamente estructural, sin criterio ni validación de contenido.
- Marca el límite entre datos externos sin garantía de forma contractual y datos internos con forma mínima gobernada.
