1. Estado
Version: v2
Estado: FROZEN
Pertenece a: Contrato_Sistema_v2
Gobernado por: Contrato_State_v2

2. Rol
Concatenar y ordenar determinísticamente las unidades contenidas en source_units y producir merged_source_units.

3. Reads
source_units

4. Writes
merged_source_units
Reglas:
Debe concatenar las unidades de todas las fuentes presentes en source_units.
Debe ordenar exclusivamente por:
(SOURCE_PRIORITY.index(source), source_seq)
El orden no puede depender del orden de finalización de ramas paralelas.
No modifica source_units.

5. Abort
FETCH_ALL_SOURCES_FAILED
UNKNOWN_SOURCE_PRIORITY

Regla:
Si todas las fuentes tienen status="failed" → emitir abort.
Si al menos una fuente tiene status="ok" → continuar.
Todas las claves de source_units MUST pertenecer a SOURCE_PRIORITY.

6. Invariantes locales
El orden resultante es total y determinista.
No elimina unidades.
No realiza deduplicación.
No transforma el payload de las unidades.