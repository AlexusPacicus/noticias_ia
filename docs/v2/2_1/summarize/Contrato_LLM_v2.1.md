# 📄 Contrato_LLM_v2.1

## 1. Estado

| Campo      | Valor                    |
|------------|--------------------------|
| Versión    | v2.1                     |
| Estado     | DRAFT                    |
| Tipo       | Contrato de Componente   |
| Componente | LLM Generation           |

**Dependencias:**

- `Contrato_SummarizePhase_v2.1`
- `Contrato_State_v2.1`

Este documento define la **interfaz contractual entre el sistema y el modelo LLM** utilizado para la generación de resúmenes.

Este contrato **NO redefine**:

- el pipeline del sistema
- el dominio del state
- la lógica de las fases

---

## 2. Contexto

El modelo LLM se utiliza exclusivamente dentro del nodo `summarize_map` de **SummarizePhase**.

Su responsabilidad es transformar el contenido textual de un item en un **resumen técnico breve**.

El LLM:

- **NO participa** en ranking
- **NO participa** en selección
- **NO modifica** el pipeline

Estas responsabilidades pertenecen a otras fases del sistema.

---

## 3. Interfaz

El LLM recibe una estructura de entrada `LLMInput` compuesta por los siguientes campos:

| Campo      | Descripción                      |
|------------|----------------------------------|
| `title`    | título del paper                 |
| `abstract` | contenido del abstract           |
| `query`    | consulta original del usuario    |

El LLM **NO DEBE recibir**:

- `ranking`
- `canonical_id`
- metadata interna del pipeline
- estructuras internas del state

---

## 4. Salida

El LLM **DEBE producir JSON válido** con el siguiente formato:

```json
{
  "summary": "string"
}
```

**Esquema de salida:**

```
LLMOutput ::= {
  summary: string
}
```

**Reglas:**

- `summary` DEBE existir
- `summary` DEBE ser `string`
- NO DEBEN existir claves adicionales

> Si el JSON contiene claves adicionales, `summarize_map` DEBE ignorarlas.  
> Si el resultado no cumple este esquema, `summarize_map` DEBE tratar el item como fallido.

---

## 5. Semántica de errores

Los errores del LLM **NO abortan el pipeline**.

**Posibles fallos:**

| Código           | Descripción                        |
|------------------|------------------------------------|
| `TIMEOUT`        | El modelo no respondió a tiempo    |
| `LLM_ERROR`      | Error interno del modelo           |
| `PARSE_ERROR`    | La respuesta no es JSON válido     |
| `EMPTY_RESPONSE` | El modelo devolvió una respuesta vacía |

Cuando ocurre un error, `summarize_map` DEBE generar un resultado fallido para el item:

```json
{
  "rank_position": X,
  "ok": false,
  "error": "PARSE_ERROR"
}
```

Esto permite mantener la correspondencia entre items de entrada y resultados generados.

---

## 6. Reglas

El uso del LLM DEBE cumplir las siguientes reglas.

### Invocación

- `summarize_map` DEBE realizar **una llamada al LLM por cada item** de entrada
- la ejecución DEBE ser **secuencial**

### Determinismo condicionado

Dado el mismo modelo, la misma configuración y el mismo input, el resultado DEBE ser estable dentro de la variabilidad del modelo.

### Separación estructural

El LLM **NO DEBE modificar** los siguientes campos estructurales:

- `rank_position`
- `title`
- `link`
- `source`

Estos campos pertenecen al pipeline estructural y son preservados por `SummarizePhase`.

### Configuración del modelo

La configuración utilizada en v2.1 es:

```
model:       llama3:8b
temperature: 0
top_p:       1

```

**Reglas:**

- esta configuración DEBE permanecer estable durante la vida de la versión v2.1
- cambios en estos parámetros NO DEBEN realizarse sin versionar el sistema

### Referencia al prompt

El prompt utilizado por el sistema se define en:

```
prompts/summarize/v2_1.txt
```

### Reglas de contenido del summary

El summary:

- DEBE basarse exclusivamente en title y abstract
- DEBE tener entre 2 y 4 frases
- NO DEBE inventar información no presente en el input

El prompt **NO forma parte del contrato**, pero su versión DEBE permanecer estable durante la vida de la versión del sistema.
