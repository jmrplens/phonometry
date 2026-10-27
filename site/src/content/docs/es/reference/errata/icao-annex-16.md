---
title: "Erratas del Anexo 16 de la OACI"
description: "Erratas del Anexo 16 de la OACI: 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre el Anexo 16 de la OACI. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Anexo 16 de la OACI, volumen I, 8.ª edición (2017), Apéndice 2, 4.4.2 (falta el signo menos del ajuste por compartición de banda)

- **Ubicación:** Apéndice 2, sección 4.4.2 (página 158 del PDF, p. APP 2-20
  impresa) del Anexo 16 de la OACI, volumen I, octava edición, julio de 2017.
- **El impreso:** «If $C_\mathrm{avg} > C(k_\mathrm{M})$, then
  $\Delta_\mathrm{B} = C_\mathrm{avg}\ C(k_\mathrm{M})$ and
  $\mathrm{PNLTM} = \mathrm{PNLT}(k_\mathrm{M}) + \Delta_\mathrm{B}$».
- **El problema:** entre las dos correcciones tonales no hay ningún operador;
  el ajuste es $\Delta_\mathrm{B} = C_\mathrm{avg} - C(k_\mathrm{M})$. La
  propia sección fija la lectura: el párrafo anterior a la fórmula pide un
  ajuste cuando $C(k_\mathrm{M})$ es menor que la media de los cinco
  espectros, la fórmula solo se aplica si $C_\mathrm{avg} > C(k_\mathrm{M})$,
  y la Nomenclatura define $\Delta_\mathrm{B}$ como «the adjustment to be
  added to the maximum PNLT», de modo que el ajuste es lo que la corrección
  tonal en PNLTM se queda por debajo de la media, un valor positivo. La capa de
  texto de la página tampoco lleva ningún carácter entre los dos términos,
  mientras que los signos menos de $(k_\mathrm{M} - 2)$ de la línea anterior
  están tanto en el impreso como en la capa de texto.
- **Evidencia:** verificado en la página 158 del PDF (p. APP 2-20 impresa) del
  Anexo 16 de la OACI, volumen I, octava edición (2017), sección 4.4.2, frente
  a la entrada de $\Delta_\mathrm{B}$ de la Nomenclatura en la página 27 del
  PDF (p. I-7 impresa) de la misma edición.
- **Comportamiento de la biblioteca:** implementa la diferencia.
  `aircraft.epnl_from_pnlt` toma $\Delta_\mathrm{B}$ como la media de las
  correcciones tonales de los registros a menos de un segundo de PNLTM menos
  la corrección tonal en PNLTM, y cero cuando eso no es positivo; los tests
  de compartición de banda de
  [`tests/aircraft/test_certification.py`](https://github.com/jmrplens/phonometry/blob/main/tests/aircraft/test_certification.py)
  fijan un caso construido a mano en 1.6 dB.
- **Estado:** sin notificar.
