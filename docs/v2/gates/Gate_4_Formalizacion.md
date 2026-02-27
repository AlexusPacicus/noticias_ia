# Gate 4 - Formalizacion v2

Estado: APROBADO (documental)  
Fecha de formalizacion: 2026-02-26

## 1) Alcance

Este Gate 4 formaliza evidencia de Gate 3.  
No modifica logica, contratos ni pipeline.

## 2) Que se valido en Gate 3

Se validaron dos frentes:

1. Estabilidad con LLM real (Ollama local) en 20 corridas con input y fetch deterministas.
2. Robustez contractual bajo fallas controladas (timeouts, JSON invalido, fallback) en 30 corridas sinteticas.

Evidencia:

1. `tests/v2/test_gate3_real_llm_stress.py`
2. `tests/v2/test_gate3_llm_stress.py`
3. `tests/artifacts/gate3_real_llm_report.json`
4. `tests/artifacts/gate3_llm_stress_report.json`

## 3) Latencias reales observadas (Gate 3 live)

Fuente: `tests/artifacts/gate3_real_llm_report.json` (20 runs)

1. Minima: `56.641057958011515 s`
2. Mediana: `72.99212812504265 s`
3. Maxima: `107.26303412497509 s`
4. Ratio `max/median`: `1.469515095398`
5. Corridas con `returned_k >= 2`: `20/20` (`1.0`)
6. Violaciones estructurales: `0`

Timestamp del artefacto: `2026-02-26 15:03:10` (hora local del entorno).

## 4) Referencia historica (opcional, no normativo)

Perfil previo no CPU (tests historicos):

1. Real: `max_latency_seconds < 15`, `latency_ratio_max_over_median < 8`, `returned_k_ge_2_ratio >= 0.9`.
2. Sintetico: `max_latency_seconds < 5`, `latency_ratio_max_over_min < 10`.
3. Estructural: sin aborts, sin excepciones escapadas, sin violaciones de output/coherencia.

Nota:
Los limites anteriores corresponden a un perfil de ejecucion distinto y
NO representan el freeze operativo actual en CPU.

## 5) Criterio de estabilidad y freeze operativo

Limites normativos (freeze CPU):

1. `max_latency_seconds <= 120` (live, end-to-end con `top_k=3`)
2. `latency_ratio_max_over_median <= 2`
3. `returned_k_ge_2_ratio >= 0.9`
4. Todas las metricas estructurales en `0` (abort/output/excepciones/coherencia)

Condiciones simultaneas de aprobacion:

1. Cero violaciones estructurales de output/summary.
2. Sin aborts ni excepciones escapadas.
3. `max_latency_seconds <= 120` y `latency_ratio_max_over_median <= 2` en perfil CPU actual.
4. `returned_k_ge_2_ratio >= 0.9`.

Resultado observado:

1. Criterio cumplido con artefacto live actual: `max=107.263034...`, `ratio=1.4695...`, `returned_k_ge_2_ratio=1.0`.

## 6) Freeze de configuracion actual LLM

Congelado sobre implementacion activa (`graph/v2/llm.py`):

1. Provider: Ollama local (`http://127.0.0.1:11434/api/generate`)
2. Modelo: `llama3:8b`
3. Temperatura: `0`
4. `max_tokens`: `450`
5. `TIMEOUT_SECONDS`: `60`
6. `MAX_RETRIES`: `1`
7. Modo de ejecucion en resumen: secuencial (iteracion por item en `summarize_map`)

Entorno operativo aceptado para este freeze: Ollama 8B en CPU.

## 9) Trazabilidad (archivo:linea)

1. Configuracion LLM actual: `graph/v2/llm.py:7-12`
2. Modo secuencial de resumen: `graph/v2/nodes/summarize_map.py:50-60`
3. Metricas y umbrales Gate 3 real: `tests/v2/test_gate3_real_llm_stress.py:205-258`
4. Metricas y umbrales Gate 3 sintetico: `tests/v2/test_gate3_llm_stress.py:210-251`
5. Latencias reales observadas: `tests/artifacts/gate3_real_llm_report.json:8-22`
6. Conteos sinteticos observados: `tests/artifacts/gate3_llm_stress_report.json:3-18`
7. Configuracion contractual LLM congelada: `docs/v2/nodos/Contrato_LLM_v2.md:10-19`

## 10) Estado contractual tras Gate 4

- Contrato_Sistema_v2: sin cambios.
- Contrato_State_v2: sin cambios.
- Diseno_v2: sin cambios.
- Contrato_LLM_v2.md: alineado con runtime congelado.
- Tests Gate 3: vigentes.
- Tests Gate 4: no aplican (Gate documental).

## 11) Partes abiertas 

1. Performance no optimizada (CPU secuencial).
2. No paralelización de summarize_map.
3. Sin backend alternativo activo (solo preparado).
4. No profiling fino por nodo.
5. Sin métricas persistidas fuera de artifacts de test.

Estas áreas quedan fuera del alcance de v2.
