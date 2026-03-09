📄 AI Papers Engine — v2.1 Scope (FROZEN)
1. Estado
Versión: v2.1
Estado: DRAFT → objetivo FROZEN tras implementación
Naturaleza: evolución estructural de v2
Modelo de ejecución: pipeline síncrono (sin persistencia)

1.1 Estructura vigente
Builders canónicos:
- `graph/v2_1/graph_21.py`
- `graph/v2_1/retrieval/graph_21.py`
- `graph/v2_1/summarize/graph_21.py`
- `graph/v2_1/hitl/graph_21.py`

Compatibilidad:
- `graph/v2/graph.py` mantiene la entrada pública legacy
- `graph/v2_1/runtime.py` es wrapper puro de compatibilidad

Ownership por capas:
- `graph/v2_1/*/graph_21.py` = builders
- `nodes/*` = ejecución pura
- `runtime/*` = utilidades LLM/parser/tipos
- `graph/v2/*` = legacy + compatibilidad

Excepciones legacy conocidas:
- `graph/v2/nodes/summarize_map.py`
- `graph/v2/nodes/filter_by_time_window.py`

2. Objetivo
Modularizar el motor v2 en fases reutilizables e introducir un nodo HITL síncrono, manteniendo:
Determinismo estructural hasta ranking
State único global
Abort dominante
Contrato público intacto
Configuración LLM congelada
v2.1 NO cambia la naturaleza del sistema.

3. Cambios estructurales incluidos

3.1 RetrievalPhase (subgrafo compilable)
Incluye:
collect_input
→ validate_input
→ fetch_*
→ merge_source_units
→ normalize
→ filter_by_time_window
→ dedupe
→ rank_bm25
→ select
Debe poder ejecutarse como:
retrieval_graph.invoke(...)
Salida mínima contractual:
ranked_items
selected_items
abort_reason (si aplica)
Prohibiciones:
No puede crear:
summary_items
summary_stats
output
Abort permitidos: A–E.
No depende del LLM.

3.2 Nodo HITL síncrono
Nodo: hitl_review
Comportamiento:
ESC → aceptar selected_items
Edit → devolver subset
Cancel → USER_ABORT
Salida HITL:
- hitl_action
- hitl_remove_keys
HITL no materializa una nueva lista de items.
Opera sobre `selected_items` mediante eliminación declarativa (`hitl_remove_keys`).

Restricciones:
No loops
No re-fetch
No re-ranking
No alteración del determinismo previo

3.3 SummarizePhase (subgrafo compilable)
Incluye:
summarize_map
→ summarize_reduce
Entrada:
selected_items

Abort permitido:
SUMMARY_ALL_ITEMS_FAILED
No conoce ranking interno.
No modifica posiciones.

3.4 RankingStrategy (estructura preparada)
Introducción de interfaz:
class RankingStrategy:
    def rank(...)
Implementación activa:
BM25Strategy
No se activan estrategias múltiples en v2.1.

3.5 execute_until
Parámetro opcional:
execute_until = "select" | "summary"
Si "select":
No se ejecuta HITL
No se ejecuta Summarize
No se crea output
No modifica contrato público estándar.

3.6 Observabilidad lateral (no contractual)
Se introduce capa de ejecución externa con:
execution_id
Métricas por fase:
retrieval_ms
hitl_ms
summarize_ms
total_ms
Restricciones:
No forman parte del state
No afectan decisiones
No alteran determinismo
No modifican contrato

4. No-Goals explícitos
v2.1 NO incluye:
Persistencia
Reanudación
Lifecycle multi-step
Multi-LLM dinámico
Nuevas fuentes
Loops adaptativos
Separación de states
Cambios en Contrato_Sistema_v2
Cambios en Contrato_LLM_v2
Estos cambios pertenecen a v3.

5. Plan de implementación
Paso 1 — Extraer RetrievalPhase
Subgrafo funcional
Tests de equivalencia con v2 hasta select
Paso 2 — Extraer SummarizePhase
Separar LLM
Confirmar equivalencia total con v2
Paso 3 — Introducir HITL
Test ESC
Test subset
Test cancel
Paso 4 — Introducir execute_until
Test "select"
Test "summary"
Paso 5 — Añadir observabilidad externa
Confirmar que el state no cambia entre ejecuciones idénticas

6. Tests mínimos obligatorios
Determinismo Retrieval sin LLM
Equivalencia v2 vs v2.1
Aborts A–E intactos
Abort F intacto
State idéntico sin métricas
Summarize no ejecuta si abort previo

7. Identidad de versiones
v2 → pipeline monolítico determinista
v2.1 → pipeline modular con HITL síncrono
v3 → orquestación con persistencia y lifecycle
🔒 Decisión arquitectónica clave
State único global
Subgrafos estructurales, no microservicios
Observabilidad externa
Sin decisiones dinámicas basadas en métricas
