1. Gemini

1.1 Input
Actúa como auditor técnico documental.

Objetivo: detectar redundancias, contradicciones, reglas duplicadas y posibles puntos de drift entre documentos contractuales v2.

Documentos a analizar:
- Contrato_Sistema_v2.md
- Contrato_State_v2.md
- Diseno_v2.md
- Runtime_v2.md
- tests_v2.md

Tarea:

1. Detecta contradicciones explícitas entre documentos.
2. Detecta reglas duplicadas que puedan generar drift futuro.
3. Detecta secciones redundantes que deberían vivir en un solo documento.
4. Señala cualquier definición repetida en más de un documento que no esté referenciada.
5. Identifica reglas que aparecen en Runtime o tests pero no están formalizadas en contratos.
6. Señala información sobrante que no aporta valor contractual ni operativo.

No opines.
No resumas.
No reformules.
Solo devuelve inconsistencias documentales reales.

Formato de salida (estricto):

{
  "status": "COHERENTE" | "INCONSISTENCIAS",
  "hallazgos": [
    {
      "tipo": "CONTRADICCION" | "REDUNDANCIA" | "REGLA_NO_FORMALIZADA" | "DUPLICACION_RIESGO_DRIFT" | "INFORMACION_SOBRANTE",
      "documentos_implicados": ["doc1", "doc2"],
      "seccion_ref": "§x.y",
      "descripcion": "explicación concreta",
      "riesgo": "ALTO | MEDIO | BAJO",
      "accion_recomendada": "breve acción correctiva"
    }
  ],
  "resumen": {
    "contradicciones": n,
    "redundancias": n,
    "reglas_no_formalizadas": n,
    "duplicaciones_riesgo_drift": n,
    "informacion_sobrante": n
  }
}

Reglas:
- Máximo 12 hallazgos.
- Prioriza riesgos altos.
- No inventes problemas si no existen.
- Si todo está coherente, devuelve status = COHERENTE.


1.2 Output

{
"status": "INCONSISTENCIAS",
"hallazgos": [
{
"tipo": "CONTRADICCION",
"documentos_implicados": [
"Contrato_Sistema_v2.md",
"Runtime_v2.md"
],
"seccion_ref": "Sistema §4.1 vs Runtime §5",
"descripcion": "Contrato_Sistema_v2 permite explícitamente la ejecución concurrente en 'fetch_*', mientras que Runtime_v2 impone la restricción estricta 'No existe paralelización'.",
"riesgo": "ALTO",
"accion_recomendada": "Aclarar si la restricción de paralelización aplica solo al entorno local o si anula el contrato, y unificar criterio."
},
{
"tipo": "REDUNDANCIA",
"documentos_implicados": [
"Contrato_Sistema_v2.md",
"Diseno_v2.md"
],
"seccion_ref": "Sistema §7.1 vs Diseño §13.1",
"descripcion": "El esquema JSON del Output Público se define íntegramente en ambos documentos. (Contrato_State_v2 sí maneja esto correctamente al referenciar Sistema §7 sin duplicar).",
"riesgo": "MEDIO",
"accion_recomendada": "Eliminar el esquema de Diseno_v2 y dejar una referencia a Contrato_Sistema_v2 §7.1."
},
{
"tipo": "REDUNDANCIA",
"documentos_implicados": [
"Contrato_Sistema_v2.md",
"Contrato_State_v2.md",
"Diseno_v2.md"
],
"seccion_ref": "Sistema §13 vs State §3 vs Diseño §14.3",
"descripcion": "La lista cerrada de 16 claves del state se enumera de forma completa y redundante en los tres documentos.",
"riesgo": "MEDIO",
"accion_recomendada": "Consolidar la lista únicamente en Contrato_State_v2 y usar referencias en los demás documentos."
},
{
"tipo": "DUPLICACION_RIESGO_DRIFT",
"documentos_implicados": [
"Contrato_Sistema_v2.md",
"Contrato_State_v2.md",
"Diseno_v2.md"
],
"seccion_ref": "Sistema §4.3 vs State §7.5 vs Diseño §5.2",
"descripcion": "La fórmula de orden determinista de merge (SOURCE_PRIORITY.index(source), source_seq) está definida contractualmente en los tres lugares de manera independiente.",
"riesgo": "BAJO",
"accion_recomendada": "Definir la fórmula en Contrato_Sistema_v2 y referenciarla en State y Diseño."
},
{
"tipo": "DUPLICACION_RIESGO_DRIFT",
"documentos_implicados": [
"Contrato_Sistema_v2.md",
"Contrato_State_v2.md",
"Diseno_v2.md"
],
"seccion_ref": "Sistema §12 vs State §7.9 vs Diseño §10.6",
"descripcion": "El orden total determinista de BM25 (-bm25_score, title ASC, link ASC) se repite explícitamente en tres documentos.",
"riesgo": "BAJO",
"accion_recomendada": "Mantener como invariante en Contrato_Sistema_v2 y referenciar en el resto."
},
{
"tipo": "DUPLICACION_RIESGO_DRIFT",
"documentos_implicados": [
"Contrato_Sistema_v2.md",
"Diseno_v2.md"
],
"seccion_ref": "Sistema §10 vs Diseño §15",
"descripcion": "Los códigos de abort y sus condiciones se enumeran en listas/tablas completas en ambos documentos.",
"riesgo": "MEDIO",
"accion_recomendada": "Centralizar la tabla de Gates y Códigos en Contrato_Sistema_v2."
},
{
"tipo": "REGLA_NO_FORMALIZADA",
"documentos_implicados": [
"Runtime_v2.md"
],
"seccion_ref": "Runtime §3",
"descripcion": "Runtime_v2 formaliza parámetros operativos del LLM (llama3:8b, temp: 0, max_tokens: 450) declarándolos FROZEN, pero hace referencia a un 'Contrato_LLM_v2.md' inexistente en el conjunto analizado, actuando como contrato de facto.",
"riesgo": "MEDIO",
"accion_recomendada": "Crear el Contrato_LLM_v2.md correspondiente o trasladar la categoría contractual de esos parámetros a Contrato_Sistema_v2."
},
{
"tipo": "INFORMACION_SOBRANTE",
"documentos_implicados": [
"Contrato_Sistema_v2.md",
"Diseno_v2.md"
],
"seccion_ref": "Sistema §14 vs Diseño §17",
"descripcion": "Diseño_v2 incluye una tabla histórica de versiones (v1, v1.1) que no tiene impacto en la arquitectura de v2 y duplica la cláusula de compatibilidad histórica ya cubierta en Sistema §14.",
"riesgo": "BAJO",
"accion_recomendada": "Eliminar Diseño §17."
}
],
"resumen": {
"contradicciones": 1,
"redundancias": 2,
"reglas_no_formalizadas": 1,
"duplicaciones_riesgo_drift": 3,
"informacion_sobrante": 1
}
}

2.