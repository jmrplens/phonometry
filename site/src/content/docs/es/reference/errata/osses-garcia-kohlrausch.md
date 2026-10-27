---
title: "Erratas de Osses, García & Kohlrausch (2016)"
description: "Erratas de Osses, García & Kohlrausch (2016): 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre Osses, García & Kohlrausch (2016). La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Osses, García & Kohlrausch (2016), modelo de intensidad de fluctuación, Ec. (3)

- **Ubicación:** Ec. (3), la transformación a razón de banda crítica (Bark)
  del frontal de patrón de excitación.
- **El impreso:**
  $z(f) = 13 \cdot \arctan(0.76 \cdot 10^{-4} \cdot f) + 3.5 \cdot \arctan((f/7500)^2)$.
- **El problema:** el primer coeficiente es el $0.76 \cdot 10^{-3}$ de
  Zwicker-Terhardt con el exponente mal impreso. Las propias anclas del
  artículo desmienten el impreso: declara
  $0.5\ \text{Bark} = 50\ \text{Hz}$ y
  $23.5\ \text{Bark} = 13.2\ \text{kHz}$ (sección 2.1.2) y
  $15\ \text{Bark} = 2.7\ \text{kHz}$ (sección 3.1), todas las cuales exigen
  $10^{-3}$. Con $10^{-4}$, $z(1\ \text{kHz}) = 1.05$ en lugar de
  $8.51\ \text{Bark}$ y los 47 centros de filtro del modelo abarcarían de
  491 Hz a 20 kHz en lugar de 50 Hz a 13.2 kHz.
- **Evidencia:** evaluación de la Ec. (3) bajo ambos exponentes contra las
  anclas Bark/frecuencia impresas del artículo. El rango impreso de la
  sección 2.1.2, «0.5 Bark (50 Hz) to 23.5 Bark (13.2 kHz)», y el ancla de la
  sección 3.1, «15 Bark (2.7 kHz)», se reproducen todos bajo el
  $0.76 \cdot 10^{-3}$ de Zwicker-Terhardt (50.6 Hz, 13.07 kHz y 2.71 kHz) y
  ninguno bajo el exponente impreso. Verificado en la página 4 del PDF (p. 4
  impresa) de Osses, García & Kohlrausch, ICA:2016, con las anclas en la
  página 7 del PDF (p. 7 impresa) del mismo artículo.
- **Comportamiento de la biblioteca:** implementa $0.76 \cdot 10^{-3}$ con
  una nota junto a la fórmula; el test de barrido de frecuencia portadora
  cazaría una regresión al valor impreso
  ([`_fluctuation_strength.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/_fluctuation_strength.py)).
- **Estado:** sin notificar (artículo de congreso, no una norma).
