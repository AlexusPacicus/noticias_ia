Contrato_LLM_v2

Estado: FROZEN
Configuracion congelada por Gate 4 (v2).
Cualquier modificacion requiere nueva formalizacion.

## 1. Rol

Definir la configuracion runtime oficial de la capa LLM consumida por `summarize_map` en v2.

## 2. Configuracion runtime congelada

- Provider: Ollama local
- Endpoint: `http://127.0.0.1:11434/api/generate`
- Modelo: `llama3:8b`
- Temperatura: `0`
- `max_tokens = 450`
- `TIMEOUT_SECONDS = 60`
- `MAX_RETRIES = 1`
- Ejecucion secuencial via `summarize_map`

## 3. Reglas de cumplimiento

- La implementacion MUST reflejar exactamente los valores de este contrato.
- No se admiten valores historicos alternativos en v2.
- Cambios de configuracion requieren nueva formalizacion de Gate.
