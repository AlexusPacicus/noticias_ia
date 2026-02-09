# Contrato de State — v1

## 1. Propósito

Definir la estructura única y contractual del estado compartido del pipeline v1. El State es la única interfaz permitida entre nodos y gobierna qué puede leerse/escribirse en cada paso.

---

## 2. Definición del State (global)

Esta lista define las únicas claves que pueden existir en el State en cualquier momento del pipeline v1. No implica orden, momento ni responsabilidad.

### 2.1 Lista cerrada

- `input_raw`
- `input`
- `fetched_items`
- `normalized_items`
- `ranked_items`
- `selected_items`
- `output`
- `abort_reason`

---

## 3. Campos prohibidos

Se consideran campos prohibidos todos aquellos no listados explícitamente en el Punto 2.

### 3.1 Prohibiciones explícitas

Queda prohibido en el State:

- Cualquier campo no listado en "Campos permitidos".
- Campos temporales, derivados o auxiliares (ej. `tmp_*`, `debug_*`).
- Metadatos de ejecución (tiempos, contadores, retries).
- Configuración del sistema o artefactos exógenos.
- Información de la fuente, si no forma parte del ítem ya normalizado.
- Estado interno del LLM o prompts.
- Flags implícitos o booleanos de control de flujo.

La aparición de cualquier campo prohibido en el State constituye **violación contractual inmediata**.

---

## 4. Ciclo de vida por campo

### Principio

Cada campo del State:

- Tiene un único creador.
- No puede ser modificado después.
- Solo puede ser leído por nodos posteriores.

### Matriz de acceso

| Campo              | Crea             | Lee                | Desde              | Hasta |
|--------------------|------------------|--------------------|---------------------|-------|
| `input_raw`        | `collect_input`  | `validate_input`   | `collect_input`     | fin   |
| `input`            | `validate_input` | todos              | `validate_input`    | fin   |
| `fetched_items`    | `fetch`          | `normalize_schema` | `fetch`             | fin   |
| `normalized_items` | `normalize_*`    | `rank`             | `normalize_schema`  | fin   |
| `ranked_items`     | `rank`           | `select`           | `rank`              | fin   |
| `selected_items`   | `select`         | `summarize`        | `select`            | fin   |
| `output`           | `summarize`      | —                  | `summarize`         | fin   |
| `abort_reason`     | cualquier nodo   | —                  | primer abort        | fin   |

- La columna **"Lee"** define una lista cerrada de nodos autorizados.
- La lectura de un campo por un nodo no listado constituye **violación contractual**.
- "Todos" se considera un alias explícito de todos los nodos posteriores del pipeline v1.
---

## 5. Invariantes del State

**1. Inmutabilidad**
Un campo, una vez creado, no puede modificarse por ningún nodo posterior.

**2. Lectura autorizada**
Un nodo solo puede leer campos para los que esté explícitamente listado en "Lee".

**3. Orden contractual**
El orden de los elementos en cualquier lista del State es contractual y no puede alterarse tras su creación.

**4. Abort dominante**
Si `abort_reason` existe:

- Ningún campo posterior puede crearse.
- `output` no puede existir.

**5. Exhaustividad**
Todo dato necesario para evaluar la corrección del resultado debe estar presente en el output final o ser deducible del contrato. Nunca de estado interno.

---

## 6. Regla de compatibilidad

Cualquier cambio en:

- campos,
- ciclo de vida,

⇒ **nueva versión del State**.

---

## 7. Estado del contrato

- **Versión:** v1
- **Estado:** **FROZEN**
