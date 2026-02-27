1. Estado
Version: v2
Estado: FROZEN
Pertenece a: Contrato_Sistema_v2
Gobernado por: Contrato_State_v2
2. Rol
Obtener unidades crudas (SourceUnit[]) desde la fuente "arxiv" y escribirlas en source_units.
3. Reads
input_validated
4. Writes
source_units["arxiv"]
Reglas:
Debe escribir únicamente la subclave "arxiv" dentro de source_units.
La estructura debe seguir el shape contractual de SourceUnit definido en Diseño v2.
Puede escribir:
status: "ok" con items: []
o status: "failed" con items: [] y error.
5. Abort
(ninguno)
Regla:
MUST NOT emitir abort_reason.
El fallo individual de fuente se modela como status="failed".