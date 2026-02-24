1. Estado
Version: v2
Estado: DRAFT
Pertenece a: Contrato_Sistema_v2
Gobernado por: Contrato_State_v2
2. Rol
Ordenar deduped_items según relevancia textual respecto a la query validada mediante BM25 y producir ranked_items con bm25_score y rank_position.
3. Reads (lista cerrada)
deduped_items
input_validated.query
4. Writes (creador único)
ranked_items
Reglas:
MUST calcular relevancia exclusivamente mediante BM25 textual.
MUST aplicar el mismo preprocesamiento a query y a cada documento.
MUST construir el texto del documento como concatenación de title y content.
MUST ordenar por:
(-bm25_score, title ASC, link ASC)
MUST asignar rank_position comenzando en 1.
MUST preservar todos los elementos de deduped_items (no elimina).
MUST retornar únicamente el delta.
MUST NOT modificar deduped_items.
5. Abort (exclusivos)
RANK_QUERY_EMPTY_AFTER_NORMALIZATION
Reglas:
Si la query queda vacía tras preprocesamiento → emitir abort_reason.
Si retorna abort_reason → no crea claves posteriores.
No lanza excepciones para abort contractual.
6. Invariantes locales
ranked_items contiene exactamente los mismos elementos que deduped_items.
Cada elemento incluye:
bm25_score
rank_position
El orden es total y determinista.
7. Prohibiciones
MUST NOT recalcular ranking en nodos posteriores.
MUST NOT emitir abort distinto al declarado.