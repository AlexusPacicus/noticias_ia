# Contrato de Nodo — `collect_input`

---

## 1. Propósito

Capturar y persistir tal cual el input del usuario como `input_raw`, sin aplicar lógica alguna.

---

## 2. Lecturas permitidas (State)

**Ninguna.**

- Este nodo no lee ningún campo del State.
- Es el primer nodo del pipeline.
- Cualquier lectura aquí sería **violación contractual**.

---

## 3. Escrituras permitidas

**Campo creado:** `input_raw`

**Regla contractual:**
`input_raw` contiene exactamente el payload recibido del usuario. No se:

- valida,
- normaliza,
- filtra,
- completa,
- reestructura.

**Inmutabilidad:**
`input_raw` se crea una única vez en este nodo. No puede ser modificado por ningún nodo posterior.

---

## 4. Invariantes locales

- No aplica ninguna lógica de negocio.
- No valida formato, tipos ni valores.
- No añade ni elimina campos.
- No transforma estructuras.
- No introduce defaults.
- No reordena claves.
- El contenido de `input_raw` es idéntico en contenido estructural al input recibido.
- Si el nodo completa su ejecución, `input_raw` existe obligatoriamente en el State.

---

## 5. Aborts específicos

### `EMPTY_INPUT_PAYLOAD`

- **Condición:** El sistema no recibe ningún payload del usuario (entrada nula / inexistente, no "inválida").
- **No incluye:**
  - Payload vacío `{}`
  - Campos faltantes
  - Valores incorrectos
  - (Eso corresponde a `validate_input`.)
El nodo señaliza abort lanzando excepción. El runtime escribe `abort_reason`.

- **Mapeo:** ↳ Abort 4 — Imposibilidad de validación ex-post (sin input no hay evaluación posible).

Este abort se evalúa antes de cualquier validación contractual.

---

## 6. Prohibiciones explícitas

Queda prohibido a este nodo:

- Leer cualquier campo del State.
- Crear cualquier campo distinto de `input_raw`.
- Modificar campos existentes del State.
- Validar formato, tipos o valores.
- Inferir intención, semántica o significado del input.
- Aplicar defaults o completar campos.
- Normalizar, filtrar o reestructurar el payload.
- Reordenar claves o alterar estructuras.
- Acceder a artefactos exógenos o configuración del sistema.
- Registrar metadatos de ejecución (timestamps, ids, logs, métricas).
- Tomar decisiones de control de flujo más allá del abort `EMPTY_INPUT_PAYLOAD`.

**Regla dura:**
Cualquier violación activa **Abort 5 — Ambigüedad de responsabilidad**.

---

## 7. Notas de gobernanza

Nodo estrictamente mecánico y de frontera. No aporta criterio, semántica ni validación.

- Su único efecto observable es la existencia de `input_raw`.
- Aísla al resto del pipeline de:
  - transporte,
  - formato de entrada,
  - canal de invocación.

**Regla de gobernanza:**
Cualquier lógica añadida aquí desplaza responsabilidad desde `validate_input` y activa **Abort 5 — Ambigüedad de responsabilidad**.

Este nodo define el límite inferior del State: todo lo anterior al pipeline queda fuera del sistema gobernado.

---

## 8. Estado del contrato

- **Versión:** v1
- **Estado:** **FROZEN**
