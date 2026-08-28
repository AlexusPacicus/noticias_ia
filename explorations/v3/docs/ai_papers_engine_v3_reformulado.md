# AI Papers Engine V3 — Reformulación Conceptual
> Estado: borrador exploratorio  
> Eje central: construcción de un espacio de configuraciones metodológicas por capas, donde la proximidad entre puntos es el mecanismo de valor.

---

## 1. Problema con la formulación anterior

El documento original planteaba v3 como un sistema para "detectar transiciones metodológicas". Esa formulación es incompleta porque no responde para qué ni para quién.

Analizar el pasado para producir un mapa del pasado no genera valor por sí solo. La comunidad investigadora ya sabe que diffusion sustituyó a GAN. Un summarizer sofisticado de historia conocida no es v3.

---

## 2. Hipótesis central reformulada

> Si existe señal estructural en cómo evolucionan las configuraciones de investigación, esa estructura puede usarse para medir proximidad entre el pasado y el presente, y esa proximidad es accionable.

Esto tiene tres capas independientes, cada una con su propia validación:

| Capa | Pregunta | Validación |
|---|---|---|
| 1 | ¿Existe señal estructural? | Experimento mínimo |
| 2 | ¿La señal forma un espacio donde la proximidad tiene significado? | Añadir planos progresivamente |
| 3 | ¿Esa proximidad es útil para el presente? | Aproximación de puntos ruidosos al espacio construido |

El documento anterior mezclaba las tres como si fueran una sola. No lo son. Son hipótesis independientes en secuencia.

---

## 3. Por qué el pasado es la base correcta

El pasado ya tiene señal consolidada. El tiempo filtró el ruido: sabes qué métodos sobrevivieron, qué configuraciones fueron adoptadas, qué líneas de investigación resultaron ser callejones sin salida.

El presente es ruidoso, incompleto y contradictorio. Los papers más recientes tienen menos citas, menos contexto, menos señal acumulada.

Pero eso no es una debilidad del diseño, es una asimetría útil:

- El espacio se construye con datos históricos **limpios por definición**
- El presente no necesita clasificarse con precisión, solo **aproximarse** al espacio ya construido
- La tolerancia al ruido del presente es alta porque el objetivo no es ubicarlo con exactitud sino identificar a qué región del espacio pasado se acerca

> El problema no es limpiar el ruido del presente. Es construir un espacio pasado lo suficientemente robusto como para que la proximidad con puntos ruidosos siga siendo informativa.

---

## 4. Estructura de planos

El espacio se construye añadiendo dimensiones de forma incremental. Cada plano nuevo no es una feature más: es una prueba de que la geometría del espacio tiene sentido.

```
Plano 1: (problem, method_family, year)
         → ¿hay estructura temporal interpretable?

Plano 2: + method_components
         → ¿la proximidad entre puntos se vuelve más precisa?

Plano 3: + dataset / metric
         → ¿los puntos cercanos en planos anteriores siguen siéndolo?

Plano N: + metadata del presente
         → ¿puedo identificar a qué configuración pasada se aproxima esto?
```

Si al añadir un plano los puntos que parecían cercanos se dispersan, ese plano no aporta señal útil o está mal definido.

---

## 5. Hipótesis de segundo orden: crecimiento exponencial

La hipótesis más fuerte de v3 no es solo que los planos añaden información, sino que la añaden de forma **no lineal**.

> Al aumentar el número de planos, la capacidad discriminativa del espacio crece de forma exponencial: de un plano se pasa a ×N planos de precisión.

Si esto es cierto:

- Dos configuraciones cercanas en el plano 1 pueden separarse claramente en el plano 3
- Dos configuraciones lejanas en el plano 1 pueden converger al añadir metadata compartida
- Con pocos planos bien elegidos se puede alcanzar una precisión que de otra forma requeriría muchos más datos

Esto convierte la triangulación no en un método de validación auxiliar, sino en el **mecanismo central del sistema**.

Lo que hay que validar entonces no es solo "¿hay señal en el plano base?" sino también:

> ¿La señal crece de forma no lineal al añadir planos?

Eso debe medirse explícitamente al pasar del plano 1 al plano 2.

---

## 6. Experimento mínimo

El experimento mínimo resuelve únicamente la **capa 1**: ¿existe señal estructural?

| Parámetro | Valor |
|---|---|
| Problema | Uno único |
| Papers | ~50–80 |
| Cobertura temporal | ~8–10 años |
| Extracción por paper | `year` + `method_family` |

**Resultado esperado — problema: text-to-image generation:**
```
2017–2020  →  GAN
2021–2022  →  diffusion
2023       →  diffusion + transformer
```

**Criterio de decisión:**
- Transición clara → hay señal → pasar a plano 2
- Sin estructura interpretable → parar, reformular o descartar

El experimento mínimo no valida v3. Solo valida que tiene sentido continuar.

---

## 7. Cuello de botella técnico

```
abstract → method_family / method_components
```

Este paso es el más crítico. Si falla, todo lo demás es arquitectura sobre ruido.

Problemas conocidos:
- Abstracts vagos o con "marketing académico"
- El mismo método con nombres distintos (`diffusion model`, `DDPM`, `score-based generative model`)
- Innovaciones reales que viven a nivel de componente, no de familia

**Estrategia de extracción — triangulación:**

| Señal | Confianza |
|---|---|
| LLM + léxico coinciden | Alta |
| Solo uno de los dos | Caso ambiguo → HITL |

Para empezar: LLM extraction + normalización léxica + HITL. Embeddings solo si son necesarios.

---

## 8. Papel del HITL

En la fase inicial, el humano no es un parche sino parte del experimento:

- Unificar sinónimos metodológicos
- Validar si la transición temporal observada tiene sentido
- Detectar si un cluster es estructura real o ruido
- Medir cuánto cambia la proximidad entre puntos al pasar al plano 2

```
máquina → extracción
humano  → normalización + validación de geometría
```

---

## 9. Qué NO hacer antes de validar señal

- Construir un repo grande antes del experimento mínimo
- Integrar ADK o MAF por adelantado
- Crear taxonomías metodológicas extensas
- Usar embeddings del abstract completo como representación principal
- Mezclar múltiples problemas desde el inicio
- Construir grafos complejos antes de confirmar estructura

> La idea se rompe si la complejidad crece antes que la evidencia.

---

## 10. Secuencia de desarrollo

```
v3.0  →  experimento mínimo (plano 1, señal)
v3.1  →  plano 2: method_components
          medir si la proximidad crece de forma no lineal
v3.2  →  plano 3: dataset / metric
          validar que la geometría se mantiene
v3.3  →  aproximación del presente al espacio construido
v3.4  →  integración ADK / MAF si el problema está validado
```

---

## 11. Hipótesis en orden

**Hipótesis 1 (capa 1):**
Existe señal estructural en `(problem, method_family, year)`.

**Hipótesis 2 (capa 2):**
Al añadir planos, la capacidad discriminativa del espacio crece de forma no lineal.

**Hipótesis 3 (capa 3):**
Un punto ruidoso del presente puede aproximarse al espacio pasado de forma informativa, sin necesidad de clasificación precisa.

Estas tres hipótesis son independientes. Confirmar la primera no implica que las otras dos sean ciertas.

---

## 12. Frase que resume v3

> v3 es un experimento para comprobar si la evolución de la investigación puede modelarse como un espacio de configuraciones metodológicas por capas, donde la proximidad entre puntos crece de forma no lineal al aumentar las dimensiones, y donde esa proximidad permite aproximar el presente al pasado de forma accionable.

---

## 13. Recordatorio crítico

Todo depende de una sola cosa primero:

> **Que exista señal suficiente en la extracción de `method_family` desde el abstract.**

Si esa parte falla, el espacio no se puede construir y el resto es irrelevante.
