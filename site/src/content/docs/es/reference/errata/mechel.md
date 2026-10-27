---
title: "Erratas de Mechel (2008)"
description: "Erratas de Mechel (2008): 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre Mechel (2008). La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Mechel (2008), Tabla 3 (una impedancia de pared que su propia Ecuación (11) no da)

- **Localización:** Tabla 3, "Density and elastic constants of materials", la
  fila "PVC, 30% softener" en la página impresa 530 (página PDF 545), frente a
  la Ecuación (11) de la página impresa 529 (página PDF 544). Fuente no
  normativa: un libro de texto.
- **Lo impreso:** la fila da $\rho$ = 1250 kg/m3, $f_{cr}d$ = 48 Hz m y
  $Z_m$ = 1220, con las columnas del módulo y del factor de pérdidas vacías.
  La Ecuación (11), en la página de enfrente, dice
  $F := f/f_{cr}\ ;\ Z_m := f_{cr}m/Z_0 = (f_{cr}d/Z_0)\,\rho$.
- **El problema:** con la densidad y el $f_{cr}d$ de la propia fila, esa
  definición da $1250 \times 48 / 413 = 145$. El 1220 impreso es 8,4 veces esa
  cifra.
- **Evidencia:** la misma expresión reproduce el resto de la tabla a lo largo
  de cuatro décadas de $Z_m$, de 20 a 1438: treinta y seis de las otras
  treinta y siete filas dentro del 5 por ciento y treinta y cuatro dentro del
  3 por ciento. La otra fila que se sale de esa banda tampoco es un defecto, y
  enseña qué aspecto tiene uno que no lo es: "Plaster board" imprime
  $Z_m$ = 85 como valor único mientras su $f_{cr}d$ es el rango de 31 a 35, y
  85 es el extremo alto de la banda que da la ecuación y no su centro. La
  conclusión no depende del valor que se tome para $Z_0$, que la ecuación
  escribe como símbolo: 400 da 150 y 415 da 144,6, frente a un 1220 impreso.
  Verificado contra la página tal como se imprime en las páginas PDF 544 y 545
  (páginas impresas 529 y 530) de Mechel (2008), *Formulas of Acoustics*,
  2.ª edición.
- **Consecuencia para las tablas del propio libro:** esa única celda. Ninguna
  otra parte del documento calcula con ella, y la densidad y el $f_{cr}d$ de
  la fila, que son las dos columnas que lee esta biblioteca, son coherentes
  entre sí.
- **Comportamiento de la biblioteca:** el catálogo guarda la densidad, el
  $f_{cr}d$ y el factor de pérdidas de cada fila, y no guarda $Z_m$, que es
  una razón de impedancia de pared y no una propiedad del material. La fila
  lleva la discrepancia en su nota. Las pruebas
  `test_the_printed_wall_impedance_follows_from_the_books_own_equation` y
  `test_the_one_row_that_does_not_is_the_one_the_errata_names` de
  [`tests/solids/test_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/solids/test_catalogue.py) fijan
  las dos mitades de la evidencia.
- **Estado:** no reportado.
