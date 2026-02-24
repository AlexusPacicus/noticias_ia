1. Estado
Version: v2
Estado: DRAFT
Pertenece a: Contrato_Sistema_v2
Gobernado por: Contrato_State_v2
2. Rol
Despachar la ejecución de los nodos fetch_* correspondientes a las fuentes activas.
3. Reads
input_validated
4. Writes
(ninguna clave propia)
Regla:
No crea claves de estado.
No modifica estado existente.
5. Abort
(ninguno)
Regla:
MUST NOT emitir abort_reason.
