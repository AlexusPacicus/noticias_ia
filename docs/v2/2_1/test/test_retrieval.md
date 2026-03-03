📄 Contrato_Test_Retrieval_v2.1
Estado: DRAFT
Tipo: Contrato de Test de Fase
Aplica a: RetrievalPhase (v2.1)


1. Scope
Este contrato define los criterios obligatorios de validación de RetrievalPhase como subgrafo estructural interno.
No define implementación de tests.
Define propiedades que MUST cumplirse.


2. Principio rector
RetrievalPhase MUST ser estructuralmente equivalente al sistema completo ejecutado hasta select.
Cualquier divergencia constituye violación contractual.


3. Equivalencia estructural
Dado:
Un input válido.
Un snapshot determinista de fuentes.
Se deben ejecutar:
system_full.invoke(..., execute_until="select")
retrieval_graph.invoke(...)
3.1 Requisito
El state resultante MUST ser deep-equal hasta selected_items.
Se exige igualdad exacta en:
Conjunto de claves existentes.
Valores.
Orden de listas.
rank_position.
bm25_score.
No se permite igualdad parcial ni tolerancia.


4. Determinismo
Dado:
Mismo input.
Mismo snapshot serializado.
RetrievalPhase MUST producir:
Idéntico ranked_items
Idéntico selected_items
Cualquier variación constituye violación.


5. Orden total
Para todos los tests nominales:
El orden MUST respetar:
(-bm25_score, title ASC, link ASC)
El test MUST verificar:
Monotonía decreciente de bm25_score.
Estabilidad en empates mediante title y link.


6. Cobertura obligatoria de aborts
Cada Gate A–E MUST tener al menos un escenario validado.
Para cada abort:
El test MUST verificar:
abort_reason correcto.
No existencia de claves posteriores.
Restricciones de valor asociadas (según Contrato_State_v2).
Ejemplos:
NO_ITEMS_IN_TIME_WINDOW → filtered_items == []
NO_ITEMS_AFTER_DEDUPE → deduped_items == []
Gate D → ranked_items MUST NOT existir.


7. Inmutabilidad del state
RetrievalPhase MUST NOT:
Sobrescribir claves existentes.
Crear claves fuera de la lista cerrada definida en Contrato_State_v2.
Crear summary_items, summary_stats o output.
El test MUST validar que no existen claves ilegales.


8. Exclusión de LLM
RetrievalPhase MUST NOT:
Invocar modelos LLM.
Depender de configuración de Contrato_LLM_v2.
El test MUST validar que ninguna clave de summarize existe en ejecución nominal.


9. Exclusiones explícitas
Este contrato NO exige testear:
Performance.
Concurrencia real.
Latencia.
Variabilidad de redacción (no aplica).
Integración con HITL.
SummarizePhase.


10. Criterio de aprobación
RetrievalPhase se considera conforme si:
Todas las propiedades anteriores se cumplen.
No existe divergencia estructural con v2.
No existen claves ilegales.
No existen variaciones de orden.