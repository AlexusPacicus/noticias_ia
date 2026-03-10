# Taxonomía v0 — Text-to-Image

> Documento heurístico para el experimento mínimo.
> No usar como taxonomía cerrada del campo.

## Objetivo

Definir un conjunto mínimo de `method_family` para clasificar papers de text-to-image
en el piloto v3.0.

La taxonomía debe servir para:
- anotación manual inicial
- reglas léxicas simples
- comparación LLM vs léxico
- visualización temporal agregada

No debe servir para capturar toda la complejidad histórica del campo.

---

## Etiquetas activas

### 1. `gan`
Usar cuando el paper pertenece principalmente a enfoques adversariales de text-to-image.

Señales típicas:
- gan
- cgan
- adversarial
- stackgan
- attngan

Incluye:
- conditional GAN
- multi-stage GAN
- attention-based GAN

No usar si:
- la difusión es claramente el núcleo metodológico

---

### 2. `autoregressive`
Usar cuando el paper modela la generación como secuencia discreta de tokens o latentes cuantizados.

Señales típicas:
- autoregressive
- token
- vq-vae
- discrete token
- dall-e
- parti

Incluye:
- transformer autoregresivo
- modelado secuencial de tokens visuales

No usar si:
- el núcleo real es difusión

---

### 3. `diffusion`
Usar cuando la familia principal es difusión/denoising.

Señales típicas:
- diffusion
- denoising
- ddpm
- score-based
- latent diffusion
- ldm
- classifier-free guidance

Incluye:
- latent diffusion
- denoising diffusion

No usar si:
- el paper se presenta claramente como rama diffusion-transformer/hybrid y eso es central para el experimento

---

### 4. `diffusion_transformer_or_hybrid`
Usar cuando el paper cae en la rama moderna donde diffusion se combina de forma central con transformer u otras variantes cercanas.

Señales típicas:
- dit
- diffusion transformer
- mm-dit
- multimodal diffusion transformer
- rectified flow
- flow matching
- sd3
- flux

Incluye:
- DiT
- SD3-like architectures
- Flux-like architectures
- variantes híbridas cercanas para este piloto

Nota:
esta categoría existe por pragmatismo experimental, no porque sea una taxonomía perfecta.

---

### 5. `other`
Usar cuando el paper sí pertenece al problema text-to-image, pero no encaja bien en las familias activas.

Ejemplos:
- métodos raros
- combinaciones no dominantes
- variantes difíciles de mapear en v0

---

### 6. `unknown`
Usar cuando no hay evidencia suficiente para clasificar con confianza.

Usar especialmente si:
- el abstract es demasiado vago
- las señales léxicas se contradicen
- LLM y heurística discrepan y no hay resolución clara

---

## Reglas de prioridad

En caso de conflicto:

1. si el núcleo metodológico es claro en el abstract, usar esa familia
2. si hay nombres de modelos famosos, tratarlos como pista, no como verdad automática
3. si varias familias aparecen pero una domina claramente, usar la dominante
4. si no domina ninguna, usar `other`
5. si falta evidencia, usar `unknown`

---

## Nivel de granularidad

Esta taxonomía v0 sacrifica precisión para ganar:
- consistencia
- velocidad de anotación
- visualización temporal clara

No separar todavía:
- gan_refined
- early_diffusion
- flow-matching como familia propia
- masked generative transformers como familia propia

Eso podría entrar en versiones posteriores si aparece señal real.

---

## Criterio de revisión futura

Revisar esta taxonomía si ocurre alguno de estos casos:
- demasiados papers caen en `other`
- demasiados papers caen en `unknown`
- una subrama nueva aparece de forma repetida
- la visualización temporal queda demasiado borrosa