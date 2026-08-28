LangGraph AI Papers Engine — v3 (Documento conceptual)
Estado: DRAFT / exploratorio
Objetivo: validar hipótesis antes de construir arquitectura.
1. Propósito de v3
Explorar si es posible detectar evolución metodológica en investigación analizando muchos papers.
v3 no busca resumir papers.
Busca identificar patrones estructurales en el espacio de investigación.
2. Hipótesis
La evolución científica puede representarse como:
(problem, method_family, year)
Si existe señal suficiente deberían aparecer transiciones como:
method_A → method_B
Ejemplo real en generación de imágenes:
GAN → diffusion → diffusion + transformer
3. Principio metodológico
Reducir el sistema al mínimo posible.
Primera representación:
(problem, method_family, year)
Planos adicionales se añaden solo si aparece señal.
4. Arquitectura v3 (exploratoria)
Pipeline reutilizando v2.1:
retrieval
→ ranking
→ method_extraction
→ temporal_analysis
Solo se modifica la fase equivalente a summarize.
5. Unidad de análisis
Cada paper se convierte en:
{
  "problem": "...",
  "method_family": "...",
  "year": "..."
}
6. Taxonomía inicial de métodos
Extremadamente reducida:
GAN
diffusion
autoregressive
transformer
other
Objetivo: reducir dimensionalidad.
7. Dataset inicial
Para evitar sobreingeniería:
1 problema
50–80 papers
8–10 años
Ejemplo de problema:
text-to-image generation
8. Extracción de método
Entrada:
title + abstract
Salida:
{
  "method_family": "..."
}
Extracción mediante LLM.
9. Estrategia de extracción (futuro)
Triangulación de señales:
LLM extraction
+
lexical normalization
+
embedding similarity
Casos ambiguos → HITL.
10. Análisis
Tabla básica:
year	method_family
2017	GAN
2018	GAN
2019	GAN
2021	diffusion
2022	diffusion
Visualización temporal.
11. Señales buscadas
aparición de métodos nuevos
sustitución metodológica
cambios en dominancia de métodos.
12. Resultados posibles
Señal clara
GAN → diffusion
→ continuar desarrollo.
Señal débil
Mejorar extracción.
Sin señal
Hipótesis no sostenida.
v3 se descarta o reformula.
13. Cuello de botella técnico
La parte crítica es:
abstract → method_family
Problemas esperados:
marketing en abstracts
sinónimos metodológicos
métodos implícitos.
14. Evolución posible de v3
Si aparece señal:
v3.1 — Representación ampliada
(problem, method_components, dataset, metric, year)
v3.2 — Configuraciones experimentales
Ejemplo:
diffusion + transformer + LAION
v3.3 — Sistema multi-agente
Integración con:
Azure AI Agent Development Kit
Microsoft Agent Framework
Agentes especializados:
problem extractor
method extractor
dataset extractor
configuration analyzer
15. Principio de desarrollo
Regla del proyecto:
hipótesis
→ experimento mínimo
→ arquitectura
Nunca al revés.
16. Valor del proyecto
v3 intenta analizar configuraciones de investigación, no papers individuales.
Unidad conceptual:
problem + configuration + time
Esto se aproxima a cómo evoluciona realmente la investigación científica.
17. Criterio de continuidad
v3 solo continúa si el experimento inicial detecta dinámica metodológica observable.
Si no aparece señal, el enfoque debe revisarse.