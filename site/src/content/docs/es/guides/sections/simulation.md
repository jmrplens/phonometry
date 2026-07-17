---
title: "Simulación de ondas"
description: "Calcular el propio campo sonoro: un solucionador FDTD acústico 2D determinista sobre una malla escalonada presión-velocidad, con fuentes, sondas de presión, obstáculos rasterizados y contornos rígidos, de impedancia o absorbentes por lado."
---

La mayor parte de esta biblioteca predice un número; esta sección calcula el
**propio campo de ondas**. Un solucionador de diferencias finitas en el
dominio del tiempo (FDTD) integra las ecuaciones acústicas lineales sobre una
malla 2D, de modo que la reflexión, la difracción, la interferencia, el
comportamiento modal y la refracción en medios inhomogéneos emergen de
primeros principios. El solucionador es determinista (entradas idénticas dan
salidas idénticas bit a bit en la misma plataforma), está validado contra
oráculos analíticos y sirve además como motor de contraste para los modelos
en forma cerrada de las demás secciones.

La única página de esta sección explica el método numérico (el esquema
leapfrog escalonado y su límite de estabilidad de Courant), los bloques de
construcción (fuentes, sondas, obstáculos y condiciones de contorno, incluido
el borde de impedancia real de reacción local), cuándo una simulación
ondulatoria merece su coste, qué puede y qué no puede decir un dominio 2D
sobre un problema 3D, y cómo la dispersión numérica fija la regla de
resolución de celdas por longitud de onda.

## Páginas de esta sección

- [Simulación de ondas FDTD 2D](/phonometry/es/guides/fdtd-simulation/): el
  método FDTD presión-velocidad en malla escalonada según el capítulo 4 de
  Attenborough y Van Renterghem (2021), sus fuentes, sondas, obstáculos y
  condiciones de contorno, los límites del 2D y la regla de dispersión
  numérica.
