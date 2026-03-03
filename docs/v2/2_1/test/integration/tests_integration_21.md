1. Scope
Valida la correcta orquestación completa de:
RetrievalPhase
→ HITL
→ SummarizePhase
No valida:
Calidad LLM
Latencia
Fetch real
Métricas
2. Objetivo
Garantizar:
Wiring correcto entre fases.
Abort dominante transversal.
Preservación de ranking.
Aplicación correcta de HITL.
No contaminación de state.
3. Casos obligatorios
3.1 Happy path completo
Sin HITL
LLM mock
output existe
ranking preservado
returned_k <= top_k
3.2 HITL subset
HITL reduce lista
Solo se resumen los seleccionados
returned_k == tamaño subset
3.3 HITL empty
HITL devuelve lista vacía
Abort SUMMARY_EMPTY_INPUT
LLM no invocado
output no existe
3.4 Abort dominante upstream
Simular:
Retrieval abort (ej: INVALID_QUERY)
Verificar:
Summarize no se ejecuta
abort_reason intacto
output no existe
4. Invariantes estructurales globales
Cada test debe verificar:
No coexistencia output + abort_reason
No creación de claves fuera de contrato
No recalculo de ranking
Determinismo estructural hasta rank_bm25