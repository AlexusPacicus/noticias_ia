# Contrato de Nodo — `validate_input`

---

## 1. Propósito

Validar el `input_raw` del usuario contra el contrato de entrada del sistema v1 y producir un `input_validated` cerrado y completo, o abortar.

Este nodo define la frontera de entrada válida al sistema gobernado.

---

## 2. Lecturas permitidas (State)

- `input_raw` (obligatorio).

**Lecturas prohibidas:**

- Cualquier otro campo del State.
- Cualquier fuente indirecta de datos (config runtime, artefactos exógenos, reloj, red, filesystem).

**Motivo contractual:**
Evitar acoplamiento semántico (Abort 3) y ambigüedad de responsabilidad (Abort 5).

---

## 3. Escrituras permitidas

**Campo creado:** `input_validated`

**Regla contractual:**
`input_validated` es el único campo que este nodo puede escribir. Contiene exclusivamente los siguientes campos contractuales:

```json
{
  "query": "string",
  "time_window": "last_24h | last_3_days | last_7_days",
  "top_k": "int"
}
```

**Reglas de escritura:**

- `input_validated` se crea una única vez en este nodo.
- La escritura es atómica:
  - o se escribe completo y válido,
  - o no se escribe y la ejecución aborta.
- `input_validated` no puede ser modificado por nodos posteriores.
- No se permite añadir:
  - campos auxiliares,
  - flags,
  - metadatos,
  - información derivada,
  - resultados parciales.

**Aplicación de defaults:**

- Si `top_k` no está presente en `input_raw`, se aplica el default contractual `top_k = 5`.
- La aplicación de defaults es una excepción explícita permitida en este nodo con el único fin de cerrar el input conforme al contrato de sistema v1.
- No se permite ningún otro tipo de completado, inferencia o ajuste de valores.

---

## 4. Invariantes locales

- `input_raw` no se modifica.
- El nodo no produce efectos colaterales fuera de la escritura de `input_validated`.
- No se crean campos auxiliares, temporales o derivados.
- No se normaliza, reescribe ni corrige ningún valor válido.
- No se infiere intención, semántica ni contexto del input.
- La validación es estricta y no interpretativa.

Si el nodo completa su ejecución sin abortar, se garantiza que:

- `input_validated` existe obligatoriamente.
- `input_validated` cumple íntegramente el contrato de entrada del sistema v1.
- No existe información necesaria para evaluar la corrección del input fuera de `input_validated`.

Todo `input_validated` que avanza en el pipeline se considera válido y definitivo para el resto de la ejecución.

---

## 5. Aborts específicos

Este nodo puede abortar únicamente por violaciones del contrato de entrada del sistema v1.

### `INVALID_QUERY`

- `query` ausente.
- Tipo distinto de `string`.
- No cumple la restricción mínima (≥ 2 palabras).
- Contiene operadores o estructura no permitida.

### `INVALID_TIME_WINDOW`

- `time_window` ausente.
- Valor fuera del enum cerrado:
  - `last_24h`
  - `last_3_days`
  - `last_7_days`

### `INVALID_TOP_K`

- `top_k` presente pero no entero.
- Valor fuera del rango `[1..10]`.

**Reglas de abort:**

- Los aborts son mutuamente excluyentes.
- El primer abort detectado detiene la ejecución.
- No se devuelven resultados parciales.
- No se escribe `input_validated`.

**Mapeo contractual:**
↳ Abort general 4 — Imposibilidad de validación ex-post.

---

## 6. Prohibiciones explícitas

Queda prohibido a este nodo:

- Leer cualquier campo distinto de `input_raw`.
- Acceder directa o indirectamente a:
  - configuración runtime,
  - artefactos exógenos,
  - reloj del sistema,
  - red, filesystem o entorno.
- Inferir intención, semántica o contexto del input.
- Normalizar, reescribir o "corregir" valores válidos.
- Crear campos auxiliares, flags, errores parciales o metadatos.
- Tomar decisiones dependientes de nodos posteriores.
- Registrar efectos colaterales (logs de negocio, métricas, contadores).
- Modificar `input_raw`.
- Escribir `input_validated` de forma parcial.

**Regla dura:**
Cualquier violación activa **Abort 5 — Ambigüedad de responsabilidad**.

---

## 7. Notas de gobernanza

Nodo de frontera contractual de entrada. Define qué inputs existen dentro del sistema gobernado. Todo lo anterior a este nodo queda fuera del alcance contractual.

- Centraliza la validación del input del usuario en un único punto auditable.
- Garantiza que el resto del pipeline opera únicamente sobre un input:
  - cerrado,
  - determinista,
  - conforme al contrato del sistema v1.

Cualquier debilitamiento, fragmentación o reinterpretación de este nodo rompe la gobernanza del sistema y activa un abort general.
