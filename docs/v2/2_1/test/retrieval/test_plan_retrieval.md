Test Plan — RetrievalPhase v2.1
Estado: DRAFT
Derivado de: Contrato_Test_Retrieval_v2.1
1. Equivalencia estructural
Objetivo:
RetrievalPhase MUST ser estructuralmente equivalente al sistema completo ejecutado hasta select.
Cubre:
Contrato §3 — Equivalencia estructural.
Test previsto:
test_equivalence_execute_until_select

2. Determinismo
Objetivo:
Mismo input + mismo snapshot → ranked_items y selected_items idénticos.
Cubre:
Contrato §4 — Determinismo.
Test previsto:
test_determinism_same_snapshot_same_output

3. Orden total congelado
Objetivo:
ranked_items MUST respetar:
(-bm25_score, title ASC, link ASC)
Cubre:
Contrato §5 — Orden total.
Test previsto:
test_total_order_respected

4. Cobertura de Gates A–E
Objetivo:
Cada Gate MUST tener al menos un escenario validado.
Cubre:
Contrato §6 — Cobertura obligatoria de aborts.
Tests previstos:
test_gate_a_invalid_input
test_gate_b_all_sources_failed
test_gate_c_no_items_in_time_window
test_gate_c_no_items_after_dedupe
test_gate_d_query_empty_after_preprocessing
test_gate_e_invalid_select_state

5. Inmutabilidad del state
Objetivo:
RetrievalPhase MUST NOT:
Crear claves fuera de la lista cerrada.
Sobrescribir claves existentes.
Cubre:
Contrato §7 — Inmutabilidad del state.
Test previsto:
test_no_illegal_keys_created

6. Exclusión LLM
Objetivo:
RetrievalPhase MUST NOT:
Invocar LLM.
Crear summary_items, summary_stats, output.
Cubre:
Contrato §8 — Exclusión de LLM.
Test previsto:
test_no_summary_keys_exist
Criterio de cierre
RetrievalPhase se considera contractualmente conforme cuando:
Todos los bloques anteriores están implementados.
No existen variaciones estructurales respecto a v2.
No existen claves ilegales.
No existen variaciones de orden.