---
title: "Erratas de Jiménez et al. (2017)"
description: "Erratas de Jiménez et al. (2017): 2 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 2 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre Jiménez et al. (2017), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Jiménez, Groby, Pagneux & Romero-García (2017), Appl. Sci. 7(6), 618, Ecs. (7)-(8)

- **Ubicación:** Ecs. (7) y (8), la densidad efectiva y el módulo de
  compresibilidad viscotérmicos de conducto rectangular (la serie de Stinson,
  usada para los cuellos y cavidades cuadrados del absorbente de ranura +
  resonador de Helmholtz).
- **El impreso:** la constante normalizadora inicial de ambas series es 4:
  $\rho_\text{eff} = -\rho_0 \cdot a^2 b^2/(4 \cdot G_\rho^2 \cdot \Sigma)$
  y el factor homólogo $4 \cdot (\gamma - 1) \cdot G_\kappa^2/(a^2 b^2)$
  dentro de $\kappa_\text{eff}$.
- **El problema:** la constante correcta es 64 (un error de factor 16). Solo
  64 reproduce los límites exactos del modelo: al desvanecerse las capas
  límite $\rho_\text{eff} \to \rho_0$ y $\kappa_\text{eff} \to \kappa_0$ (el
  4 impreso da $16 \cdot \rho_0$), y en continua el
  $j\omega \cdot \rho_\text{eff}$ del conducto cuadrado tiende a la
  resistividad de flujo de Poiseuille exacta de Shah-London: el valor de la
  serie $a^6/(64 \cdot S_0) = 28.4542$ casa con $fRe/2 = 28.455$ (en unidades
  de $\eta/a^2$), donde $S_0$ es la suma doble de modos transversales a
  $G = 0$; el 4 impreso da dieciséis veces eso.
- **Evidencia:** evaluación de ambas constantes contra los límites sin capa
  límite y el valor exacto de conducto cuadrado de Shah-London; el límite de
  conducto ancho de la serie también casa con el propio modelo de ranura de
  los artículos (Ec. (6)) solo con 64.
- **Comportamiento de la biblioteca:** implementa 64 con una nota en el
  docstring; los límites están fijados en
  [`tests/materials/absorbers/test_slow_sound.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/absorbers/test_slow_sound.py)
  y la comprobación de conformidad «Poiseuille limit (Stinson 1991)».
- **Estado:** sin notificar (artículo de revista, no una norma).

## Jiménez et al. (2017), Appl. Sci. 7(6), 618 / Sci. Rep. 7, 5389, término de radiación de la ranura

- **Ubicación:** Appl. Sci. Ec. (3), la impedancia de radiación
  característica de las ranuras, y la reimpresión idéntica en los Methods del
  artículo de metadifusores (Sci. Rep. 7, 5389, Ec. (5)).
- **El impreso:**
  $Z_{\Delta l_\text{slit}} = -i\omega \cdot \Delta l_\text{slit} \cdot \rho_0/(\phi t \cdot S_0)$.
- **El problema:** el término modela la masa de radiación añadida de la boca
  de la ranura, pero el prefactor $-i\omega$ impreso es una expresión del
  convenio temporal opuesto ($\mathrm{e}^{-i\omega t}$), inconsistente con la cadena
  de matrices de transferencia por lo demás en $\mathrm{e}^{+i\omega t}$ de los
  artículos (las matrices de ranura con $+i$ fuera de la diagonal de la
  Appl. Sci. Ec. (2) y la impedancia de resonador tipo cotangente con $-i$).
  Transcrita literalmente en esa cadena, la corrección sube la resonancia del
  panel de ranuras donde una masa añadida debe bajarla: para una ranura de
  1 mm con paso de red de 30 mm y periodo de 50 mm el pico de absorción se
  mueve de 378.6 Hz a 386.8 Hz tal como está impreso, contra 370.8 Hz con el
  signo de masa. Las correcciones de extremo de cuello del mismo modelo se
  comportan correctamente (bajan la resonancia del resonador).
- **Evidencia:** evaluación numérica de ambos signos de la corrección contra
  el panel sin corregir; la dirección de las correcciones de extremo de
  cuello de los mismos artículos como control consistente.
- **Comportamiento de la biblioteca:** usa el signo de masa añadida
  ($+j\omega$ en el convenio $\mathrm{e}^{+j\omega t}$ de la biblioteca), conjugando
  el término impreso exactamente igual que conjuga la serie de conducto de
  Stinson de los artículos; dirección y pico están fijados por
  ``test_slit_radiation_correction_lowers_resonance`` en
  [`tests/materials/absorbers/test_slow_sound.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/absorbers/test_slow_sound.py).
- **Estado:** sin notificar (artículos de revista, no normas).
