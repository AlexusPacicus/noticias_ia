# Timeline — Text-to-Image Generation

> Documento heurístico para exploración inicial.  
> No usar como ground truth histórico ni como taxonomía cerrada.

## Objetivo

Tener una línea temporal operativa para el piloto v3.0, de forma que sirva para:

- orientar la taxonomía inicial
- elegir ventanas temporales
- definir reglas léxicas mínimas
- comprobar si el stacked area muestra un cambio histórico visible

No debe usarse para forzar etiquetas ni para justificar resultados que aún no hayan aparecido en el experimento.

---

## 1. Línea temporal resumida

### 2016 — Inicio moderno del campo
**Hito:** Reed et al., *Generative Adversarial Text to Image Synthesis*  
**Familia dominante:** GAN  
**Valor histórico:** arranque moderno de text-to-image con deep learning  
**Idea clave:** conditional GAN condicionado por embeddings de texto  
**Resultado:** primeras imágenes plausibles, pero aún limitadas en calidad y diversidad

---

### 2017 — Mejora jerárquica
**Hito:** StackGAN  
**Familia dominante:** GAN  
**Idea clave:** generación en dos etapas  
**Resultado:** mejora clara en resolución y realismo

---

### 2018 — Atención sobre el texto
**Hito:** AttnGAN  
**Familia dominante:** GAN + attention  
**Idea clave:** atención a nivel palabra-región  
**Resultado:** mejor alineación texto-imagen y más detalle fino

---

### 2019–2020 — Refinamiento incremental
**Familia dominante:** GAN refinado  
**Idea clave:** mejoras sobre estabilidad, alineación y detalle  
**Resultado:** progreso incremental, pero sin ruptura clara de paradigma  
**Lectura útil para el piloto:** fase de plateau / refinamiento

---

### 2021 — Cambio de paradigma
**Hitos simbólicos:** DALL·E, GLIDE, Latent Diffusion  
**Familias en juego:** autoregressive + early diffusion  
**Idea clave:** el campo deja de depender solo de GANs  
**Resultado:** aparece una transición real, todavía mixta

**Nota importante:**  
2021 no debe etiquetarse de forma rígida como un único bloque.  
Es una fase híbrida donde conviven:
- GAN tardío
- autoregressive
- difusión temprana

---

### 2022 — Consolidación de diffusion
**Hitos simbólicos:** DALL·E 2, Imagen, Stable Diffusion  
**Familia dominante:** diffusion  
**Idea clave:** diffusion pasa a dominar el campo práctico y académico  
**Resultado:** salto fuerte en calidad, control y adopción

---

### 2023 — Puente hacia diffusion + transformer
**Hitos simbólicos:** SDXL, DiT  
**Familia dominante:** diffusion  
**Subrama relevante:** diffusion + transformer  
**Idea clave:** DiT funciona como puente conceptual hacia arquitecturas posteriores tipo SD3 / Flux  
**Resultado:** la rama diffusion sigue dominando, pero empieza a cambiar su forma interna

**Nota para el piloto:**  
DiT debe tratarse como hito simbólico de transición, no como inicio absoluto del campo.

---

### 2024 — Madurez de diffusion-transformer
**Hitos simbólicos:** SD3, Flux.1  
**Familia dominante:** diffusion + transformer / hybrid  
**Idea clave:** consolidación de arquitecturas de tipo diffusion-transformer  
**Resultado:** el campo entra en una etapa de madurez arquitectónica más híbrida

**Nota para el piloto:**  
Variantes tipo flow-matching / rectified-flow pueden entrar aquí como parte de la misma rama amplia, no como familia separada todavía.

---

### 2025 — Continuidad de la madurez
**Familia dominante:** diffusion + transformer / hybrid  
**Idea clave:** menos ruptura de paradigma y más consolidación, optimización y variantes  
**Resultado:** la frontera ya no es solo “generar imagen desde texto”, sino controlar, abaratar, personalizar y hacer más eficiente el sistema

---

## 2. Mapeo heurístico a `method_family` simple

> Esto es una simplificación operativa para el experimento mínimo.  
> No es una taxonomía definitiva del campo.

| Rango temporal | method_family dominante | Nota |
|---|---|---|
| 2016–2018 | `gan` | cGAN, StackGAN, AttnGAN |
| 2019–2020 | `gan_refined` | refinamiento incremental |
| 2021 | `autoregressive` / `early_diffusion` | fase híbrida |
| 2022 | `diffusion` | consolidación clara |
| 2023–2025 | `diffusion_transformer_or_hybrid` | DiT, SD3, Flux, variantes cercanas |

---

## 3. Porcentajes orientativos para el piloto

> Estimación heurística para exploración.  
> No usar como dato histórico exacto.

| Rango temporal | Dominio aproximado | Interpretación útil |
|---|---|---|
| 2016–2018 | GAN > 80% | dominio claro |
| 2019–2020 | GAN refinado ~70–80% | plateau incremental |
| 2021 | mix | transición real |
| 2022 | diffusion > 70% | cambio fuerte |
| 2023–2025 | diffusion + transformer / hybrid > 80% | madurez de la nueva rama |

**Uso práctico:**  
Si el clasificador LLM + léxico acierta aproximadamente en un rango razonable y el stacked area enseña el cambio histórico de forma visible, hay señal suficiente para seguir explorando.

---

## 4. Léxico inicial por familia

> Estas palabras clave son solo señales débiles iniciales.  
> No bastan por sí solas para clasificación final.

### `gan`
- adversarial
- gan
- cgan
- stackgan
- attngan

### `autoregressive`
- autoregressive
- token
- discrete token
- vq-vae
- dall-e
- parti

### `diffusion`
- diffusion
- denoising
- score-based
- ddpm
- latent diffusion
- ldm
- classifier-free guidance

### `diffusion_transformer_or_hybrid`
- dit
- diffusion transformer
- mm-dit
- multimodal diffusion transformer
- rectified flow
- flow matching
- sd3
- flux

---

## 5. Riesgos de sesgo interpretativo

### Riesgo 1 — Forzar la cronología
Que la línea temporal sugiera una secuencia no significa que cada paper encaje limpiamente en ella.

### Riesgo 2 — Confundir modelo famoso con familia
`SD3`, `Flux`, `DALL·E` y similares son pistas útiles, pero no equivalen automáticamente a una familia metodológica pura.

### Riesgo 3 — Sobrefragmentar demasiado pronto
Separar demasiado pronto:
- diffusion
- diffusion-transformer
- flow-matching
- rectified-flow
- masked generative
puede romper el experimento inicial.

### Riesgo 4 — Convertir narrativa en verdad
Esta nota existe para orientar el piloto, no para decidir de antemano lo que el experimento “debe encontrar”.

---

## 6. Recomendación operativa para v3.0

Para el primer experimento:

- problema único: `text-to-image generation`
- ventana temporal: `2016–2025`
- taxonomía mínima:
  - `gan`
  - `gan_refined`
  - `autoregressive`
  - `early_diffusion`
  - `diffusion`
  - `diffusion_transformer_or_hybrid`
  - `other`
  - `unknown`

Si esta taxonomía resulta demasiado fina para el volumen inicial, simplificar a:

- `gan`
- `autoregressive`
- `diffusion`
- `diffusion_transformer_or_hybrid`
- `other`
- `unknown`

---

## 7. Criterio de utilidad de esta nota

La nota habrá sido útil si ayuda a:

- construir una taxonomía mínima razonable
- crear reglas léxicas iniciales
- revisar discrepancias LLM vs léxico
- interpretar visualmente una transición temporal real

La nota habrá sido un problema si se usa para:

- imponer etiquetas
- justificar manualmente cualquier salida
- convertir la hipótesis en conclusión antes del experimento