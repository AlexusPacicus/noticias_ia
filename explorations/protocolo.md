Protocolo v3.0
Objetivo
Validar solo la hipótesis 1: si existe señal estructural mínima en (problem, method_family, year) para un único problema. No validar proximidad completa, ni ADK, ni MAF, ni planos extra todavía.
Qué entra
1 problema único
50–80 papers
8–10 años
extracción mínima por paper:
title
year
abstract
method_family 
ai_papers_engine_v3_reformulado
Qué no entra
múltiples problemas
grafo complejo
embeddings como representación principal
taxonomías grandes
integración ADK/MAF
plano 2 o 3 antes de validar señal
Pregunta exacta
¿Se observa una transición temporal interpretable de familias metodológicas dentro de un solo problema? 
ai_papers_engine_v3_reformulado
Hipótesis nula
No hay estructura interpretable; lo extraído desde abstract es demasiado ruidoso.
Si ocurre eso, se para o se reformula.
Dataset mínimo
Cada fila:
paper_id
title
year
abstract
method_family_llm
method_family_lexical
method_family_final
confidence
review_status
notes
Método de extracción
Triangulación mínima:
LLM propone method_family
regla léxica propone method_family
si coinciden: alta confianza
si no coinciden: ambiguo → HITL
Taxonomía inicial
Empieza con 5–10 familias, no más.
Ejemplo genérico:
GAN
diffusion
transformer
retrieval-based
graph-based
reinforcement-learning
contrastive
hybrid
other
unknown
Crítica: si haces una taxonomía “bonita” de 25 etiquetas, te cargas el experimento. Todavía no estás clasificando el mundo; estás midiendo si hay señal.
Criterio de éxito
Hay señal si:
al menos ~70% de los papers quedan en una familia interpretable tras normalización
los ambiguos no dominan la muestra
aparece una secuencia temporal legible por años o bloques de años
esa secuencia tiene sentido para humano sin forzar narrativa 
ai_papers_engine_v3_reformulado
Criterio de fracaso
Fracasa si:
unknown/other domina
LLM y léxico discrepan demasiado
necesitas demasiada intervención manual para casi todo
la transición temporal solo aparece “si la cuentas bonito”
Output esperado
Algo así:
2017–2019 -> family_A domina
2020–2022 -> family_B crece
2023–2025 -> family_B + family_C
No necesitas geometría avanzada todavía. Solo una transición legible.
Estructura de trabajo
Dentro del repo actual, pero aislado:
explorations/v3/
  experiment_001.py
  data/
    raw/
    interim/
    curated/
  outputs/
  notes.md
Orden de ejecución
elegir un problema único
reunir 50–80 abstracts
definir taxonomía mínima
correr extracción LLM + léxico
revisar ambiguos manualmente
agrupar por año
decidir: señal / no señal
Decisión posterior
si hay señal: pasar a v3.1 y añadir method_components
si no hay señal: reformular extracción o abandonar esa línea
