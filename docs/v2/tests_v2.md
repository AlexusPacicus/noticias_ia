# Tests v2

## 1. Scope

Este documento describe las suites de test que validan v2.
No sustituye a los contratos ni a Gate 4.

---

## 2. Test Matrix

| Suite        | Tipo            | Valida                                                     | Artefactos        |
|--------------|-----------------|------------------------------------------------------------|--------------------|
| unit         | Unit            | Semántica local de nodos y shape de outputs              | pytest logs        |
| integration  | Integration     | Encadenamiento entre nodos y consistencia de state       | pytest logs        |
| gate3_synth  | E2E sintético   | Determinismo estructural sin dependencia del backend LLM | snapshot outputs   |
| gate3_real   | E2E real        | Ejecución nominal en perfil CPU local con LLM            | run_*.json         |

---

## 3. Gates

### Gate 3

Valida ejecución real del pipeline en entorno CPU local:

- Sin aborts en escenario nominal
- Con estructura final completa
- Latencias observadas dentro del umbral aprobado en Gate 4

### Gate 4

Formaliza:

- Freeze operativo
- Freeze LLM
- Estado contractual resultante

---

## 4. Criterios de aprobación

Los criterios normativos viven en Gate 4.
Las suites de test verifican que dichos criterios se cumplen.

---

## 5. Cobertura y límites

No se testea:

- Optimización de performance
- Carga concurrente
- SLA
- Backend alternativo
- Comportamiento en entorno distinto al perfil CPU local

La validación se realiza exclusivamente en entorno CPU local.