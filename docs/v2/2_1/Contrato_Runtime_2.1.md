# 📄 Contrato_Runtime_v2.1

## 1. Identificación

Sistema: AI Papers Engine  
Versión: v2.1  
Estado: FROZEN
Tipo: Contrato de Runtime  

Dependencias:

- `Contrato_Sistema_v2.1`  
- `Contrato_State_v2.1`  
- `Contrato_RetrievalPhase_v2.1` 
- `Contrato_HITLPhase_v2.1`  
- `Contrato_SummarizePhase_v2.1`  

Este documento define:

- el modelo de ejecución del sistema  
- la propagación del state  
- la semántica de abort  
- la semántica de ejecución parcial  

Este contrato **NO redefine**:

- el dominio del state  
- los contratos de fase  
- la lógica interna de los nodos  

Las palabras clave **DEBE**, **NO DEBE** y **PUEDE** deben interpretarse según RFC 2119.

---

# 2. Modelo de ejecución

El sistema se ejecuta como una **máquina de estados determinista**.

Cada nodo se ejecuta bajo el siguiente modelo conceptual:

node(state_actual) → actualización_parcial_del_state

Reglas:

- cada nodo recibe el state completo actual  
- cada nodo devuelve únicamente las claves que actualiza  
- el runtime incorpora dichas actualizaciones al state global  

Los nodos **NO DEBEN mutar el state directamente**.

La ejecución del sistema es:
- síncrona
- secuencial
- determinista


---

# 3. Orden de ejecución del pipeline

El runtime **DEBE ejecutar exactamente el pipeline definido por el sistema**.

Orden obligatorio:
collect_input
→ validate_input
→ fetch_router
→ fetch_arxiv
→ fetch_huggingface
→ merge_source_units
→ normalize
→ filter_by_time_window
→ dedupe
→ rank_bm25
→ select
→ hitl_review
→ summarize_map
→ summarize_reduce

Reglas:

- el orden **NO DEBE cambiar**
- no se permiten nodos adicionales
- no se permiten loops
- no se permite branching dinámico

---

# 4. Propagación del state

El runtime mantiene **un único state global**.

Regla conceptual de propagación:
state_siguiente = state_actual + actualización_del_nodo

donde:
actualización_del_nodo = resultado devuelto por el nodo ejecutado

El runtime:

- **DEBE aplicar las actualizaciones de forma determinista**
- **DEBE respetar el writer único definido en Contrato_State_v2.1**

La gobernanza del state se rige exclusivamente por:
`Contrato_State_v2.1`

---

# 5. Semántica de abort

El runtime aplica **abort dominante**.

Regla:
Si existe abort_reason en el state, la ejecución DEBE detenerse inmediatamente.

Semántica:

1. un nodo puede emitir `abort_reason`
2. el runtime detecta su presencia en el state
3. el runtime **NO DEBE ejecutar nodos posteriores**
4. el state se devuelve inmediatamente

Regla adicional:
El runtime DEBE verificar la presencia de abort_reason
después de cada ejecución de nodo.

El conjunto válido de abort codes está definido en:
`Contrato_Sistema_v2.1`

---

# 6. Semántica de routing

El sistema utiliza **routing estático**.

Las transiciones entre nodos están:
- predefinidas
- determinadas por el pipeline
- sin branching dinámico

El runtime **NO DEBE introducir decisiones semánticas**.

El runtime únicamente ejecuta el orden de nodos definido por el sistema.

---

# 7. Semántica de ejecución parcial

El runtime admite ejecución parcial mediante el parámetro:
execute_until

Valores permitidos:
- select
- summary

---

### execute_until = select

El runtime **DEBE ejecutar únicamente RetrievalPhase**.

No deben ejecutarse los nodos:
- hitl_review
- summarize_map
- summarize_reduce

No deben crearse las claves:
- hitl_action
- hitl_remove_keys
- summary_items
- summary_stats
- output

---

### execute_until = summary

El runtime **DEBE ejecutar el pipeline completo**.

El resultado **DEBE ser equivalente a una ejecución estándar del sistema**.

---

# 8. Entry y Exit points

El runtime define los siguientes puntos de ejecución.

ENTRY_NODE:
- collect_input

EXIT_NODE:
- summarize_reduce

Fronteras de fase:
RetrievalPhase → select
HITLPhase → hitl_review
SummarizePhase → summarize_reduce


---

# 9. State retornado

El runtime **DEBE devolver el state completo acumulado**.

### Ejecución completa exitosa

El state **DEBE contener**:
- summary_items
- summary_stats
- output

---

### Ejecución parcial

El state **DEBE contener**:
- ranked_items
- selected_items

---

### Abort

El state **DEBE contener**:
- abort_reason

Las reglas de existencia de claves se rigen por:
`Contrato_State_v2.1`