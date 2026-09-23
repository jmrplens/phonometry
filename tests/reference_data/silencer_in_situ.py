#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Printed oracles for a silencer measured where it stands (ISO 11820:1996).

ISO 11820:1996 prints no worked example of its own, so every number here was
read on the printed page of some other document that computes one of its
quantities. Each table names the document, the edition, the PDF page it was
read on and the printed folio, because that citation is the reason the number
can be trusted. The documents themselves are not in this repository; the
numbers are.

Three families of source, and they are not of equal weight:

* **ISO 14163:1998 Annex B** prints the one-third-octave to octave conversion
  of clause 9.1.5 as a worked table, in the sister standard on silencer
  guidelines. It is the only oracle here that comes from an ISO document.
* **Holgado Palacios (2014)**, a master's thesis at the Universidad
  Politécnica de Madrid, measured three splitter silencers in a reverberation
  suite following UNE-EN ISO 11820 and printed the whole reduction: six
  microphone positions per band, the reverberation times, the areas and the
  resulting insertion loss. It is measured data, so its three silencers are
  one campaign and not three independent checks.
* **Textbooks and engineering guidelines** (Barron 2003, Bies, Hansen and
  Howard 2017, Ver and Beranek 2006, VDI 2081 Blatt 2, Fuchs 2013, INSHT NTP
  668) print worked examples of the closed forms ISO 11820 shares with the
  rest of the field: the energy mean, the background subtraction, the Sabine
  area, the area term of a sound power, the ideal gas law and the area scaling
  of a flow velocity.

Two things read on those pages are deliberately **not** here, and the reason
is recorded so that a later pass does not pick them up by mistake:

* the ``S_II`` and ``S_I`` columns of Holgado Palacios, Tablas LXIV to LXVI.
  They are a quarter of the Sabine absorption, the quantity of Equations (6),
  (10) and (12), but the thesis computed them with a Sabine constant of about
  0,161, that is a speed of sound near 343 m/s, where ISO 11820 prints 340 and
  this library follows the standard. Recomputing them at 340 m/s misses the
  printed column by up to 0,10 m2, and no single volume and speed reproduce
  all 42 entries of one table, so the columns are inputs to Equation (21) here
  and never expected values. The ratio is what Equation (21) uses, and every
  constant factor cancels in it;
* Example 2-2 of Barron (2003), folio 17, which prints 1,184 kg/m3 for air at
  25 C and 101,3 kPa. Barron works there at 298,2 K, a 273,2 offset, where
  Equation (29) prints 273 + theta. The four figures he prints hide the
  difference, so the example agrees with the module without being evidence for
  it. Example 8-8, folio 372, is the same trap made visible: 1,292 kg/m3 for
  air at 10 C and 105 kPa comes out of 283,15 K, and Equation (29) gives
  1,293.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# ISO 14163:1998 Annex B (informative), Table B.1
# ---------------------------------------------------------------------------
# "Example of the conversion of attenuations in one-third-octave bands to the
# attenuation in the corresponding octave band". Read on the printed page of
# UNE-EN ISO 14163:1999 (ISO 14163:1998), PDF page 47, printed folio "- 47 -",
# and cross-checked cell for cell on BS EN ISO 14163:1998, PDF page 50,
# printed folio 40. The two prints carry identical numbers.
#
# The table folds the 50, 63 and 80 Hz one-third octaves into the 63 Hz
# octave, for three spectra that share one one-third-octave attenuation of
# 3, 12 and 21 dB. It is the worked example ISO 11820 clause 9.1.5 does not
# print: fold the levels on each side and take the difference afterwards, and
# the octave attenuation depends on the spectrum.

#: The one-third-octave attenuation the three spectra share, in decibels.
ISO14163_TABLE_B1_THIRD_OCTAVE_ATTENUATION_DB: tuple[float, float, float] = (
    3.0,
    12.0,
    21.0,
)

#: The three spectra, as (source levels, attenuated levels) in decibels over
#: the 50, 63 and 80 Hz one-third octaves.
ISO14163_TABLE_B1_THIRD_OCTAVE_DB: dict[str, tuple[tuple[float, ...], ...]] = {
    "laboratory pink noise": ((90.0, 90.0, 90.0), (87.0, 78.0, 69.0)),
    "axial fan": ((84.0, 88.0, 93.0), (81.0, 76.0, 72.0)),
    "centrifugal fan": ((93.0, 88.0, 84.0), (90.0, 76.0, 63.0)),
}

#: The 63 Hz octave levels the table prints, as (source, attenuated) in
#: decibels. Every cell of Table B.1 is a whole decibel.
ISO14163_TABLE_B1_OCTAVE_DB: dict[str, tuple[float, float]] = {
    "laboratory pink noise": (95.0, 88.0),
    "axial fan": (95.0, 83.0),
    "centrifugal fan": (95.0, 90.0),
}

#: The octave-band attenuation row of Table B.1, in decibels. It is the
#: difference of the two printed octave levels above it, which is why the
#: centrifugal fan reads 5 dB where the unrounded difference is 4,41 dB.
ISO14163_TABLE_B1_OCTAVE_ATTENUATION_DB: dict[str, float] = {
    "laboratory pink noise": 7.0,
    "axial fan": 12.0,
    "centrifugal fan": 5.0,
}

# ---------------------------------------------------------------------------
# Holgado Palacios (2014), TFM, Universidad Politécnica de Madrid
# ---------------------------------------------------------------------------
# Elena Holgado Palacios, "Diseño de laboratorio de ensayo para la evaluación
# de silenciadores in situ", Trabajo Fin de Máster, Máster en Ingeniería
# Acústica de la Edificación y Medio Ambiente, E.T.S.I. y Sistemas de
# Telecomunicación, Universidad Politécnica de Madrid, 2014 (oa.upm.es record
# 35222). Spanish. Three splitter silencers of Transformados Acuter, types
# 100-200, 150-200 and 200-200, measured on 29/11/2013 in the two adjacent
# reverberation rooms of the laboratory, six microphone positions, one-third
# octaves from 50 Hz to 5000 Hz.
#
# The thesis prints its own Equation (47), which is Equation (21) of
# EN ISO 11820:1996 character for character:
#     D_is = Lp_II - Lp_I + 10 log (S_II / S_I) + K_II - K_I  [dB]

#: The receiving room volume, in cubic metres, printed as "V: 201,23 m3" on
#: the laboratory data sheet of Anexo II, printed folio 228 (PDF page 256).
#: The body prose rounds it to 201 and misprints the unit as m2 twice, so the
#: data sheet is the figure to cite.
HOLGADO_ROOM_VOLUME_M3: float = 201.23

# Tabla XL, printed folio 121 (PDF page 149): "Nivel de ruido recibido en las
# distintas posiciones de micrófono con silenciador de Tipo 100-200 de
# Transformados Acuter instalado en sistema". Six positions per band and the
# energy mean of them, which the table heads "L_Is medio".
#
# The mean column is the plain energy mean of the six raw position levels: no
# background is taken off, which the thesis's own background table (Tabla
# XLII, folio 123) confirms, since its mean column is a plain energy mean of
# six positions where by construction no correction can apply. Do not cite it
# as a worked example of the thesis's Equations (35) and (36), which are the
# background-corrected mean of ISO 11820 Equations (17) and (18).

#: Tabla XL, row by row as the page prints it: the one-third-octave centre in
#: hertz against the six microphone positions in decibels and the mean of
#: them, which the table heads "L_Is medio".
HOLGADO_TABLE_XL: dict[float, tuple[tuple[float, ...], float]] = {
    50.0: ((64.3, 60.3, 62.3, 65.3, 47.3, 56.4), 61.9),
    63.0: ((65.3, 61.0, 61.0, 57.6, 60.0, 61.1), 61.6),
    80.0: ((71.1, 69.2, 67.7, 66.4, 69.5, 61.8), 68.4),
    100.0: ((70.0, 64.8, 62.3, 62.5, 60.4, 63.1), 65.1),
    125.0: ((66.8, 61.2, 62.4, 54.8, 54.5, 57.1), 61.7),
    160.0: ((62.8, 53.2, 54.9, 51.7, 50.8, 51.0), 56.7),
    200.0: ((52.2, 48.1, 44.8, 46.3, 46.4, 47.0), 48.2),
    250.0: ((48.5, 46.3, 42.6, 42.0, 42.3, 42.2), 44.8),
    315.0: ((45.3, 40.8, 40.2, 40.3, 37.8, 38.6), 41.3),
    400.0: ((39.9, 34.6, 34.0, 33.3, 34.0, 32.4), 35.6),
    500.0: ((32.8, 32.5, 29.1, 28.7, 27.5, 28.4), 30.3),
    630.0: ((29.8, 26.6, 28.0, 24.5, 25.0, 25.5), 27.0),
    800.0: ((27.9, 24.6, 25.2, 21.5, 22.0, 23.1), 24.6),
    1000.0: ((24.9, 24.2, 21.9, 22.0, 21.6, 21.8), 22.9),
    1250.0: ((20.2, 18.8, 17.0, 16.8, 18.1, 17.5), 18.2),
    1600.0: ((20.0, 19.1, 19.2, 17.4, 19.0, 18.5), 18.9),
    2000.0: ((20.9, 18.8, 18.4, 17.8, 19.7, 18.1), 19.1),
    2500.0: ((20.5, 20.0, 19.0, 18.2, 19.3, 18.6), 19.3),
    3150.0: ((26.6, 24.1, 22.6, 21.3, 22.4, 21.6), 23.5),
    4000.0: ((31.4, 27.4, 26.4, 24.2, 24.0, 23.8), 27.2),
    5000.0: ((37.0, 33.8, 35.3, 30.8, 31.9, 31.2), 33.9),
}

# Tablas LXIV, LXV and LXVI: the summary of each of the three tests and the
# insertion loss computed from it, on printed folios 145, 148 and 150 (PDF
# pages 173, 176 and 178). Each row below is one printed row: the
# one-third-octave centre in hertz against TR_c medio (the reverberation time
# with the substitution duct, in seconds), Lp_II Correg. (the received level
# with the duct, in decibels), TR_s medio (the reverberation time with the
# silencer), Lp_I Correg. (the received level with the silencer) and D_is (the
# insertion loss the thesis computes from them). The S_II and S_I columns the
# tables print between the levels and D_is are left out for the reason given
# in the module docstring; the K_II - K_I column is left out because it is
# zero in every band of all three tables. The two runs were at nearly the same
# temperature, 21,9 C with the silencer against 23,2 C with the duct per the
# Anexo II data sheets, and Equation (20) gives -0,010 dB for that pair. So
# these tables exercise the level difference and the area term of Equation
# (21) and not the field-correction term.
#
# The printed D_is cannot be pinned to the last printed digit from these
# summary columns: the thesis computed it from unrounded spreadsheet means and
# printed its inputs rounded to 0,1 dB and 0,01 s. Recomputing from the
# printed inputs stays inside the interval that rounding allows, about
# 0,13 dB, in every band of all three tables.

#: One row of a summary table: reverberation time without the silencer in
#: seconds, level without it in decibels, reverberation time with it, level
#: with it, and the insertion loss the thesis prints.
HolgadoRow = tuple[float, float, float, float, float]

#: Tabla LXIV, printed folio 145: the 100-200 silencer, 600 x 600 x 900 mm.
HOLGADO_TABLE_LXIV: dict[float, HolgadoRow] = {
    50.0: (2.46, 66.3, 3.14, 61.9, 5.4),
    63.0: (3.56, 65.7, 3.49, 61.6, 4.0),
    80.0: (2.09, 73.5, 1.61, 68.4, 3.9),
    100.0: (1.78, 70.7, 1.94, 65.1, 6.0),
    125.0: (1.99, 71.0, 1.96, 61.7, 9.2),
    160.0: (1.90, 67.3, 1.88, 56.7, 10.6),
    200.0: (1.64, 63.7, 1.65, 48.2, 15.5),
    250.0: (1.78, 65.6, 1.75, 44.8, 20.8),
    315.0: (1.87, 61.2, 1.82, 41.3, 19.9),
    400.0: (1.77, 55.1, 1.77, 35.6, 19.6),
    500.0: (1.79, 53.1, 1.83, 29.8, 23.5),
    630.0: (1.91, 51.2, 1.89, 26.4, 24.8),
    800.0: (1.91, 52.6, 1.88, 23.6, 29.0),
    1000.0: (1.93, 53.6, 1.91, 22.4, 31.2),
    1250.0: (1.94, 49.9, 1.93, 16.9, 32.9),
    1600.0: (1.87, 56.0, 1.90, 17.6, 38.4),
    2000.0: (1.82, 59.8, 1.84, 17.8, 42.1),
    2500.0: (1.74, 62.1, 1.74, 18.3, 43.8),
    3150.0: (1.56, 63.4, 1.60, 23.5, 40.0),
    4000.0: (1.37, 62.3, 1.41, 27.2, 35.2),
    5000.0: (1.11, 60.9, 1.18, 33.9, 27.2),
}

#: Tabla LXV, printed folio 148: the 150-200 silencer. The thesis contradicts
#: itself on its front dimension, 750 x 600 x 900 mm beside Figura 15 and
#: 700 x 600 x 900 mm in the results heading.
HOLGADO_TABLE_LXV: dict[float, HolgadoRow] = {
    50.0: (2.30, 66.7, 2.66, 63.8, 3.5),
    63.0: (3.54, 65.5, 3.43, 62.9, 2.5),
    80.0: (1.92, 72.8, 1.77, 67.7, 4.8),
    100.0: (1.77, 70.8, 1.94, 65.8, 5.4),
    125.0: (1.98, 70.5, 1.96, 65.3, 5.2),
    160.0: (1.89, 67.2, 1.93, 60.0, 7.3),
    200.0: (1.63, 63.1, 1.59, 52.4, 10.7),
    250.0: (1.79, 64.7, 1.73, 51.0, 13.6),
    315.0: (1.82, 61.2, 1.87, 47.7, 13.6),
    400.0: (1.75, 55.2, 1.71, 40.6, 14.4),
    500.0: (1.80, 52.6, 1.79, 36.1, 16.4),
    630.0: (1.89, 51.2, 1.87, 33.3, 17.8),
    800.0: (1.89, 52.5, 1.89, 31.9, 20.7),
    1000.0: (1.92, 53.3, 1.92, 31.0, 22.3),
    1250.0: (1.94, 49.8, 1.97, 24.3, 25.6),
    1600.0: (1.87, 55.7, 1.88, 26.1, 29.6),
    2000.0: (1.83, 59.6, 1.83, 28.8, 30.8),
    2500.0: (1.74, 62.0, 1.73, 32.5, 29.4),
    3150.0: (1.60, 63.3, 1.57, 38.8, 24.5),
    4000.0: (1.41, 62.6, 1.39, 43.5, 19.0),
    5000.0: (1.16, 60.9, 1.13, 50.9, 9.9),
}

#: Tabla LXVI, printed folio 150: the 200-200 silencer, 800 x 600 x 900 mm.
HOLGADO_TABLE_LXVI: dict[float, HolgadoRow] = {
    50.0: (2.14, 67.1, 2.06, 64.8, 2.2),
    63.0: (3.52, 65.4, 3.35, 62.5, 2.7),
    80.0: (1.74, 72.3, 1.63, 69.4, 2.6),
    100.0: (1.75, 70.9, 1.92, 67.5, 3.8),
    125.0: (1.96, 70.0, 1.92, 67.2, 2.7),
    160.0: (1.87, 67.0, 1.93, 62.9, 4.3),
    200.0: (1.62, 62.6, 1.59, 54.1, 8.4),
    250.0: (1.80, 64.1, 1.70, 53.3, 10.5),
    315.0: (1.78, 61.1, 1.82, 50.5, 10.7),
    400.0: (1.74, 55.2, 1.71, 44.1, 11.1),
    500.0: (1.81, 52.1, 1.78, 39.4, 12.7),
    630.0: (1.88, 51.2, 1.86, 36.6, 14.6),
    800.0: (1.88, 52.5, 1.88, 35.0, 17.5),
    1000.0: (1.90, 52.9, 1.90, 35.3, 17.6),
    1250.0: (1.95, 49.7, 1.91, 28.5, 21.1),
    1600.0: (1.87, 55.4, 1.87, 29.8, 25.6),
    2000.0: (1.84, 59.4, 1.85, 34.3, 25.1),
    2500.0: (1.75, 61.9, 1.74, 42.7, 19.2),
    3150.0: (1.63, 63.3, 1.61, 49.8, 13.4),
    4000.0: (1.45, 62.9, 1.43, 51.3, 11.5),
    5000.0: (1.21, 60.9, 1.19, 54.8, 6.0),
}

#: The three tests, keyed by the silencer type the thesis names. One campaign,
#: one room, one operator and one spreadsheet, so sixty-three bands of one
#: oracle rather than three oracles of twenty-one.
HOLGADO_INSERTION_TESTS: dict[str, dict[float, HolgadoRow]] = {
    "100-200": HOLGADO_TABLE_LXIV,
    "150-200": HOLGADO_TABLE_LXV,
    "200-200": HOLGADO_TABLE_LXVI,
}

# ---------------------------------------------------------------------------
# Barron (2003), Industrial Noise Control and Acoustics
# ---------------------------------------------------------------------------
# Randall F. Barron, "Industrial Noise Control and Acoustics", Marcel Dekker,
# 2003. The electronic edition shows no running heads on its pages, so every
# folio below was recovered from the text layer and corroborated by the
# constant offset of twelve against its neighbours; the PDF page is what a
# reader can check directly.

# Table 3-4, "Background noise correction factors", PDF page 84, folio 72.
# The page prints the rule it feeds, L(corrected) = L(measured) - A_Delta with
# Delta L = L(measured) - L(background), and Eq. (3-48) on the facing page is
# the logarithmic subtraction itself. At one measuring point ISO 11820
# Equations (17) and (18) reduce to exactly that subtraction.
#
# Note what the table is *not*: an oracle for ISO 11820 Table 1. That table is
# stepped and integer-indexed and deliberately not the logarithmic
# subtraction, and it takes off 2,0 dB at a 5 dB margin where Barron prints
# 1,7 and 1,0 dB at 8 dB where Barron prints 0,7.

#: Table 3-4: the correction to subtract, in decibels, by the margin of the
#: measured level over the background, in decibels.
BARRON_TABLE_3_4_DB: dict[float, float] = {
    1.0: 6.9,
    1.5: 5.3,
    2.0: 4.3,
    2.5: 3.6,
    3.0: 3.0,
    3.5: 2.6,
    4.0: 2.2,
    4.5: 1.9,
    5.0: 1.7,
    5.5: 1.4,
    6.0: 1.3,
    6.5: 1.1,
    7.0: 1.0,
    7.5: 0.9,
    8.0: 0.7,
    9.0: 0.6,
    10.0: 0.5,
    12.0: 0.3,
    14.0: 0.2,
    16.0: 0.1,
    18.0: 0.1,
    20.0: 0.0,
}

#: Example 3-6, PDF page 85, folio 73: a fan measured at 83 dB against a 77 dB
#: background, corrected to 81,7 dB by Eq. (3-48) and again, to the same
#: figure, by the 1,3 dB Table 3-4 gives at a 6 dB margin.
BARRON_EXAMPLE_3_6_DB: tuple[float, float, float] = (83.0, 77.0, 81.7)

#: Example 3-4, PDF page 77, folio 65: nine 500 Hz octave levels on a
#: parallelepiped measurement surface around an air compressor, in decibels,
#: and the mean the book computes from them with its Eq. (3-32), which is
#: ISO 11820 Equation (2).
BARRON_EXAMPLE_3_4_LEVELS_DB: tuple[float, ...] = (
    82.0,
    81.2,
    82.6,
    79.6,
    80.1,
    76.7,
    79.8,
    80.6,
    78.1,
)
BARRON_EXAMPLE_3_4_MEAN_DB: float = 80.4

#: The same example: the measurement surface, 2,60 m by 2,80 m by 1,60 m high,
#: printed as S_m = 17,28 + 7,28 = 24,56 m2, and the 10 log10 of it that the
#: solution on folio 66 prints as the first term of its sound power.
BARRON_EXAMPLE_3_4_AREA_M2: float = 24.56
BARRON_EXAMPLE_3_4_AREA_TERM_DB: float = 13.90

#: Example 3-3, PDF pages 72 to 74, folios 60 to 62: ten levels on a
#: hemisphere of radius 1,250 m about a motor, in decibels, with the
#: measurement surface the book prints as 9,817 m2 and the characteristic
#: impedance of the room air, 411,6 rayl. The book's Eq. (3-30) reaches
#: L_W = 90,4 dB, which is the mean level plus 10 lg(S/S_0) plus the impedance
#: correction -10 lg(rho c / 400).
BARRON_EXAMPLE_3_3_LEVELS_DB: tuple[float, ...] = (
    86.0,
    81.5,
    82.4,
    81.3,
    70.9,
    72.9,
    68.0,
    79.3,
    78.5,
    80.1,
)
BARRON_EXAMPLE_3_3_AREA_M2: float = 9.817
BARRON_EXAMPLE_3_3_IMPEDANCE_RAYL: float = 411.6
BARRON_EXAMPLE_3_3_SOUND_POWER_DB: float = 90.4

#: Example 8-11, PDF page 399, folio 387, and Example 8-10, PDF page 392,
#: folio 380: the density of the air flowing through a muffler, as
#: (temperature in degrees Celsius, ambient pressure in pascals) against the
#: printed density in kilograms per cubic metre. Example 8-11 prints both
#: 450 K and 177 C, which is 273 + theta exactly as Equation (29) writes it;
#: Example 8-10 prints 600 K and 620 F and no Celsius, so its 327 C is the
#: standard's own offset applied to Barron's kelvin and the row corroborates
#: rather than discriminates.
BARRON_MUFFLER_GAS_DENSITY: dict[str, tuple[float, float, float]] = {
    "Example 8-11, air at 450 K and 140 kPa": (177.0, 140_000.0, 1.084),
    "Example 8-10, air at 600 K and 110 kPa": (327.0, 110_000.0, 0.639),
}

#: Example 5-7, PDF page 215, folio 203: a 900 mm square main duct, whose
#: cross-section of 0,810 m2 the book turns into an area-equivalent diameter
#: of 1,016 m with D = (4 S / pi)^(1/2). That root is the half of ISO 11820
#: Equation (15) this anchors; the 1,5 diameters the equation puts in front of
#: it are the standard's own and appear nowhere on Barron's page.
BARRON_EXAMPLE_5_7_AREA_M2: float = 0.810
BARRON_EXAMPLE_5_7_EQUIVALENT_DIAMETER_M: float = 1.016

#: Example 7-2, PDF pages 297 to 299, folios 285 to 287, section 7.3: a
#: 6,20 m by 6,00 m by 3,10 m room at 21 C, so c = 343,8 m/s, whose 500 Hz
#: equivalent absorption area is computed twice by two unrelated routes (the
#: Eyring expression and the Fitzroy relationship) and then turned into a
#: reverberation time with T = 55,26 V / (c a). The printed constant 55,26 is
#: 4 x 6 ln 10, so the book's absorption area a is four times the S of
#: Equations (6), (10) and (12).
BARRON_EXAMPLE_7_2_VOLUME_M3: float = 115.32
BARRON_EXAMPLE_7_2_SPEED_M_S: float = 343.8
BARRON_EXAMPLE_7_2_ABSORPTION_M2: dict[float, float] = {0.459: 40.41, 0.981: 18.89}

# ---------------------------------------------------------------------------
# Other printed sources
# ---------------------------------------------------------------------------

#: Bies, Hansen and Howard, "Engineering Noise Control", 5th edition, CRC
#: Press, 2017, Section 1.10.4, Example 1.4 and Solution 1.4, PDF page 65,
#: printed folio 36: a machine measured at 92,0 dB against an 88,0 dB
#: background, which the solution subtracts in energy to 89,8 dB. The 3 dB the
#: text asks for there is a floor on the margin, not the cap on the correction
#: that ISO 11820 9.1.1 and 9.1.2 state.
BIES_EXAMPLE_1_4_DB: tuple[float, float, float] = (92.0, 88.0, 89.8)

#: Ver and Beranek (eds.), "Noise and Vibration Control Engineering", 2nd
#: edition, Wiley, 2006, Section 4.7, Example 4.2, PDF pages 95 and 96,
#: printed folios 90 and 91: a 200 m3 room at 21,4 C, so c = 344 m/s, whose
#: 100 Hz reverberation time of 3 s gives an equivalent absorption area of
#: 10,7 m2 by A = (55,26/c)(V/T_rev). The first term of the sound power that
#: follows is printed as 10 log(A/A_0) = 10,3 dB.
#:
#: The example's own final answer, 106,4 dB, does not follow from its printed
#: terms: the bracket 10,3 + 0,22 + 1,62 - 0,3 - 6 sums to 5,84 and the total
#: should read 105,8 dB. The slip is a sign carried on the impedance term, and
#: it is why only the area and its decibel term are taken from this page.
VER_BERANEK_EXAMPLE_4_2_VOLUME_M3: float = 200.0
VER_BERANEK_EXAMPLE_4_2_REVERBERATION_TIME_S: float = 3.0
VER_BERANEK_EXAMPLE_4_2_SPEED_M_S: float = 344.0
VER_BERANEK_EXAMPLE_4_2_ABSORPTION_M2: float = 10.7
VER_BERANEK_EXAMPLE_4_2_AREA_TERM_DB: float = 10.3

#: VDI 2081 Blatt 2:2005-05, "Tabelle 1. Stroemungsgeraeuschberechnung",
#: element 2 "Kulissenschalldaempfer", PDF page 12, printed folio "- 12 -": a
#: splitter silencer of five 200 mm splitters and five 100 mm gaps in a
#: 1,500 m by 0,600 m housing, carrying 16 000 m3/h. The housing and gap
#: cross-sections are not printed; they follow from the printed geometry,
#: which closes exactly (5 x 0,200 + 5 x 0,100 = 1,500 m), and are confirmed
#: twice over by the printed face velocity of 4,94 m/s and the printed
#: hydraulic diameter of 0,171 m.
VDI2081_SPLITTER_VOLUME_FLOW_M3_H: float = 16_000.0
VDI2081_SPLITTER_HOUSING_AREA_M2: float = 0.9
VDI2081_SPLITTER_FREE_AREA_M2: float = 0.3
VDI2081_SPLITTER_GAP_VELOCITY_M_S: float = 14.81

#: Fuchs, "Applied Acoustics: Concepts, Absorbers, and Silencers for
#: Acoustical Comfort and Noise Control", Springer, 2013, Table 13.4, PDF page
#: 588, printed folio 574: the airway velocity of two splitter designs at
#: three flow rates and three housing cross-sections, as
#: (volume flow in m3/h, housing cross-section in m2, velocity of design a,
#: velocity of design b) in metres per second. Design (a) is one thick
#: splitter with a blockage ratio m = 2 and design (b) two thin ones with
#: m = 0,5, both printed beside Fig. 13.25 on folio 542; Eq. (13.1) on folio
#: 510 turns m into the free cross-section, S_s = S / (1 + m).
#:
#: Every printed velocity is truncated towards zero rather than rounded, which
#: is visible where 66,67 prints as 66 and 16,67 as 16.
FUCHS_TABLE_13_4: tuple[tuple[float, float, int, int], ...] = (
    (20_000.0, 0.75, 22, 11),
    (40_000.0, 0.75, 44, 22),
    (40_000.0, 1.50, 22, 11),
    (60_000.0, 0.75, 66, 33),
    (60_000.0, 1.50, 33, 16),
    (60_000.0, 2.25, 22, 11),
)

#: The two blockage ratios of Fig. 13.25, printed on folio 542.
FUCHS_BLOCKAGE_RATIOS: dict[str, float] = {"a": 2.0, "b": 0.5}

#: Instituto Nacional de Seguridad e Higiene en el Trabajo, Nota Técnica de
#: Prevención NTP 668, "Medición del caudal en sistemas de extracción
#: localizada", 2004, Ec. 2 on PDF page 3 and Ec. 3 on the first line of PDF
#: page 4. The web-published note carries no printed folio. The two equations
#: are ISO 11820 Equation (28) with the unit conversion folded into the
#: coefficient: v = 4,43 (P_D/d)^(1/2) with the velocity pressure in
#: millimetres of water column, and v = 4,04 (P_D)^(1/2) once the density is
#: fixed at the 1,2 kg/m3 the note states for air at 20 C and 1 atm.
NTP668_VELOCITY_COEFFICIENTS: dict[str, tuple[float, float]] = {
    "Ec. 2, density free, 1 kg/m3": (1.0, 4.43),
    "Ec. 3, air at 20 C, 1,2 kg/m3": (1.2, 4.04),
}

#: The conventional millimetre of water column, in pascals: water of
#: 1000 kg/m3 under the standard gravity of 9,806 65 m/s2. It is the
#: definition of the unit and not something the note prints.
MILLIMETRE_WATER_COLUMN_PA: float = 9.806_65
