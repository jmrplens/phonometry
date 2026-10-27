---
title: "Erratas de Southall et al. (2019)"
description: "Erratas de Southall et al. (2019): 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre Southall et al. (2019). La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Southall et al. (2019), Aquatic Mammals 45(2), Tabla 7 (SPL de pico impulsivo)

*Artículo de revista con revisión por pares, no una norma.*

- **Ubicación:** Tabla 7 (p. 156 impresa), los criterios de umbral TTS y PTS
  para ruido impulsivo; las dos filas de carnívoros en el aire PCA y OCA.
- **El impreso:** PCA SPL de pico TTS 138 y SPL de pico PTS 144; OCA SPL de
  pico TTS 161 y SPL de pico PTS 167
  $\text{dB re } 20\ \mu\text{Pa}$.
- **El problema:** los cuatro son errores tipográficos. Las propias erratas
  de los autores (*Aquatic Mammals* 45(5), 569-572,
  DOI 10.1578/AM.45.5.2019.569) nombran los cuatro en la p. 569 impresa,
  «There are four typographical errors in Table 7 on page 156», y reimprimen
  la tabla corregida en la p. 570 impresa: PCA 155 y 161, OCA 170 y 176. Las
  mismas erratas corrigen además la columna encabezada «B» de la Tabla 5 al
  parámetro b de la Ec. (2), que igualmente llaman error tipográfico.
- **Evidencia:** las erratas mismas, que nombran cada valor erróneo y su
  sustituto, corroboradas por la propia regla de extrapolación del artículo.
  Nótese primero lo que *no* discrimina. La regla de pico PTS = pico TTS +
  6 dB de la p. 155 impresa la satisface también el par impreso
  ($144 - 138 = 6$, igual que $161 - 155 = 6$), así que no dice nada sobre
  qué par es el correcto. Tampoco la duplicación visible en las filas
  impresas, donde la entrada de SPL de pico TTS es igual a la entrada **SEL**
  de umbral PTS de la misma fila (PCA 123 / 138 / 138 / 144 y OCA 146 / 161 /
  161 / 167, leyendo SEL TTS, pico TTS, SEL PTS, pico PTS): para estas dos
  filas en el aire esa igualdad la fuerzan dos reglas que el artículo declara
  en la p. 155 impresa, ambas sumando 15 dB al mismo SEL TTS base, así que se
  cumpliría fueran cuales fueran los valores SEL. Una revisión anterior de
  esta entrada leía esa igualdad como la firma de un corrimiento de columna;
  es en cambio la tabla impresa siendo internamente consistente con el propio
  método en el aire del artículo, que es lo que hace de las erratas lo único
  que zanja el asunto.
  - **El valor.** Los números corregidos están cerca de lo que produce la
    regla de extrapolación del artículo, con la salvedad de que la regla no
    se declara para estas filas. La p. 155 impresa fija el umbral TTS de SPL
    de pico impulsivo de un grupo sin datos directos en el umbral de audición
    a la frecuencia de mejor sensibilidad $f_0$ más 159 dB, y restringe esa
    regla explícitamente a los grupos en el agua: «For other species groups
    **in water** (LF, SI, PCW, and OCW), 159 dB was added to the value of the
    hearing threshold at f₀». La desarrolla para PCW: «Peak SPL TTS onset was
    estimated as 212 dB re 1 µPa (53 dB at f₀ + 159 dB)». Evaluar el
    audiograma de grupo de la Tabla 2 en el $f_0$ de la Tabla 4 reproduce las
    tres filas en el agua que las erratas no tocan (SI 219.6 contra un 220
    publicado; PCW 212.5 contra 212; OCW 226.1 contra 226), lo que valida la
    regla donde el artículo la aplica. Extenderla a las dos filas de
    carnívoros en el aire, cosa que el artículo no hace, da PCA
    $-4.6\ \text{dB re } 20\ \mu\text{Pa}$ a 2.3 kHz y OCA
    $11.4\ \text{dB re } 20\ \mu\text{Pa}$ a 10 kHz, de donde **154.4** y
    **170.4**. Esos reproducen los corregidos 155 y 170 con margen de 0.6 dB
    y quedan a 16 dB y 9 dB de los impresos 138 y 161, que es lo que los hace
    corroborantes y no confirmatorios; nótese que 154.4 redondea a 154, no a
    155, y una revisión anterior de esta entrada afirmaba que redondeaba al
    valor corregido.
  - **Una segunda inconsistencia, sin reparar.** La p. 155 impresa declara
    que para los carnívoros en el aire específicamente «a nominal 15 dB
    offset is used ... between the SEL-based TTS threshold and the peak
    SPL-based threshold», lo que reproduce los *impresos* 138 y 161 desde la
    columna SEL. Esa frase, no la regla de +159 dB, es la que el propio
    método del artículo aplica a PCA y OCA. Las erratas resuelven el
    conflicto a favor de valores consistentes con la regla de +159 dB, así
    que dejan sin efecto la frase además de la tabla; la frase queda en pie
    en el artículo.
  Verificado en la página 31 del PDF (p. 155 impresa) y la página 32 del PDF
  (p. 156 impresa) de Southall et al. (2019), Aquatic Mammals 45(2), que
  llevan la restricción «in water (LF, SI, PCW, and OCW)», el desplazamiento
  de 15 dB en el aire en el mismo párrafo, las dos formulaciones de la regla
  de +6 dB, y la Tabla 7 del artículo con la fila PCA 123 / 138 / 138 / 144 y
  la fila OCA 146 / 161 / 161 / 167. Las erratas son una publicación propia,
  *Aquatic Mammals* 45(5), 569-572, encuadernada al final de la copia que
  distribuyen los autores: verificadas allí en la página 109 del PDF (p. 569
  impresa), que nombra los cuatro valores y sus sustitutos, y la página 110
  del PDF (p. 570 impresa), que reimprime la Tabla 7 con PCA 123 / 155 / 138
  / 161 y OCA 146 / 170 / 161 / 176.
- **Comportamiento de la biblioteca:** los valores corregidos por las erratas
  son los implementados en
  [`bioacoustics/weighting.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/underwater/bioacoustics/weighting.py),
  fijados por `test_southall_table_7_errata_values_are_implemented`, con la
  propia regla de +159 dB comprobada contra el audiograma en
  `test_southall_impulsive_peak_spl_is_threshold_at_f0_plus_159_db` para los
  grupos en el agua a los que el artículo la restringe y, por separado y con
  la extrapolación etiquetada como tal, para PCA y OCA.
- **Estado:** notificado por los propios autores (erratas publicadas en
  2019).
