# Contrato de State - v1.1

## 1. Proposito

Definir el state gobernado del runtime LangGraph para v1.1.

Este contrato complementa `docs/v1.1/Contrato_Sistema_v1.1.md`.

## 2. Claves permitidas

### 2.1 Input publico (entrada al grafo)

- `query`
- `time_window`
- `top_k` (opcional)

### 2.2 State interno contractual del pipeline

- `input_raw`
- `input_validated`
- `external_units`
- `normalized_items`
- `ranked_items`
- `selected_items`
- `output`
- `abort_reason`

No se permiten claves adicionales fuera de esta lista cerrada.

## 3. Reglas operativas

- No hay mutacion in-place de state en nodos.
- Cada nodo retorna solo su delta (`dict` parcial).
- LangGraph realiza el merge de estado.
- Cada campo tiene un unico creador contractual.

## 4. Abort dominante

Si existe `abort_reason`:

- El flujo redirige a `END`.
- No se crean campos posteriores.
- `output` no puede coexistir con `abort_reason` en una ejecucion abortada.

## 5. Exposicion externa

- El output publico se limita a `OutputState`.
- Campos internos del pipeline no se exponen al consumidor.

## 6. Estado del contrato

- Version: v1.1
- Estado: ACTIVE
