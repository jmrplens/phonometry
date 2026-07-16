---
title: "Ruido de rotorcraft: el método del hemisferio"
description: "El modelo de fuente por hemisferio de ruido de helicópteros de ECAC Doc 32 / NORAH2 y sus ajustes de propagación: ensanchamiento esférico, absorción atmosférica (ISO 9613-1 / Tabla 4) y el efecto de suelo de Chien-Soroka sobre suelo de impedancia CNOSSOS."
---

El ruido de los helicópteros es muy directivo, así que el método de **ECAC
Doc 32** describe la fuente con un **hemisferio de ruido**: niveles de presión
sonora en bandas de 1/3 de octava sobre una malla esférica de azimut `φ` y ángulo
polar `θ`, definidos a una distancia de referencia fija de **60 m** en condiciones
atmosféricas de referencia de la ICAO. Situar esa fuente en un receptor añade el
ajuste de propagación `ΔLp = ΔLs + ΔLa + ΔLg`.

## El hemisferio de ruido

Un `RotorcraftHemisphere` contiene los niveles de banda sobre la malla
azimut/polar. `hemisphere_source_level` lee el nivel en una dirección de emisión
arbitraria: primero rellena los huecos de la malla desde los bins llenos
angularmente más cercanos (Ec. 14/15, con caché) y después interpola de forma
bilineal en el dominio de energía sobre los cuatro bins vecinos (Ec. 13), de modo que las
celdas parcialmente medidas se mantienen continuas con sus esquinas medidas.

```python
import phonometry as ph

h = ph.RotorcraftHemisphere(frequencies=freqs, azimuth=phi, polar=theta, levels=levels)
lv = ph.hemisphere_source_level(h, 0.0, 90.0)   # nivel de fuente por banda a 60 m
h.plot()                                          # directividad proa-popa
```

## Ajustes de propagación

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rotorcraft_ground_effect_es.svg" alt="Ajuste por efecto de suelo de rotorcraft frente a la frecuencia de 1/3 de octava para suelo duro y blando, con refuerzo a baja frecuencia, un valle de interferencia profundo y la región incoherente de alta frecuencia" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rotorcraft_ground_effect_es_dark.svg" alt="Ajuste por efecto de suelo de rotorcraft frente a la frecuencia de 1/3 de octava para suelo duro y blando, con refuerzo a baja frecuencia, un valle de interferencia profundo y la región incoherente de alta frecuencia" style="width:82%">

El nivel del hemisferio a 60 m se lleva al receptor con tres ajustes (§A.4):
`spherical_spreading_adjustment` (`ΔLs = −20·log10(r/60)`, Ec. 24),
`atmospheric_adjustment` (`ΔLa = −α(f)·(r − 60)` con el coeficiente de
ISO 9613-1, Ec. 26/27) y `ground_effect_adjustment` (interferencia directo/
reflejado sobre un plano de impedancia, Chien-Soroka Ec. 28-35, con la impedancia
de Delany-Bazley y las clases de resistividad de flujo CNOSSOS `"A"`-`"H"`).

```python
import numpy as np
import phonometry as ph

freqs = 1000.0 * 10.0 ** (np.arange(-13, 11) / 10.0)   # tercios 50 Hz-10 kHz
r = 500.0
recibido = (lv
            + ph.spherical_spreading_adjustment(r)
            + ph.atmospheric_adjustment(freqs, r)
            + ph.ground_effect_adjustment(freqs, 150.0, 1.5, 500.0, flow_resistivity="D"))
```

La base de datos estándar está registrada a 60 m, el valor por defecto. Si un
hemisferio usa otra distancia polar (`h.distance`, p. ej. anillos de hover a
70 m), pásala a los dos ajustes dependientes de la distancia como
`reference_distance=h.distance`.

Validado contra la Tabla 4 de la guía NORAH2 (las 31 bandas), el ensanchamiento
inverso al cuadrado de forma cerrada, los límites analíticos de suelo rígido y
rasante del efecto de suelo, consultas bilineales fuera de nodo sobre los
hemisferios de referencia de los once tipos de helicóptero, y de extremo a
extremo contra los historiales de evento único del prototipo NORAH2 (0.1 dB(A)
sobre suelo duro, 0.5 dB sobre suelo blando).

## Referencias

- European Civil Aviation Conference. (2026). *Report on standard method of
  computing rotorcraft noise contours* (ECAC.CEAC Doc 32, 1.ª ed.).
  [Página de documentos de ECAC](https://www.ecac-ceac.org/documents/ecac-documents-and-international-agreements),
  [PDF gratuito](https://www.ecac-ceac.org/images/documents/ECAC-CEAC-DOC_32-REPORT_ON_STANDARD_METHOD_OF_COMPUTING_ROTORCRAFT_NOISE_CONTOURS.pdf).
  El método estándar de contornos de rotorcraft cuyo modelo de fuente por
  hemisferio y ajustes de propagación implementa esta página.
- Olsen, H., Tuinstra, M., & van Oosten, N. (2024). *Rotorcraft noise
  modelling guidance* (Research Project NOISE SC01, entregable D1.5d,
  contrato EASA.2020.FC.06). European Union Aviation Safety Agency.
  [Página del proyecto en EASA](https://www.easa.europa.eu/en/research-projects/environmental-research-rotorcraft-noise),
  [PDF gratuito](https://www.easa.europa.eu/en/downloads/132005/en).
  La guía a nivel de ecuación (Ec. 13-35) tras la implementación, con los
  valores de atenuación de la Tabla 4 y los hemisferios de referencia usados
  como oráculos.
- Chien, C. F., & Soroka, W. W. (1975). Sound propagation along an impedance
  plane. *Journal of Sound and Vibration*, 43(1), 9-20.
  [doi:10.1016/0022-460X(75)90200-X](https://doi.org/10.1016/0022-460X(75)90200-X).
  La solución de interferencia de dos rayos sobre un plano de impedancia tras
  el ajuste de efecto de suelo.
- Delany, M. E., & Bazley, E. N. (1970). Acoustical properties of fibrous
  absorbent materials. *Applied Acoustics*, 3(2), 105-116.
  [doi:10.1016/0003-682X(70)90031-9](https://doi.org/10.1016/0003-682X(70)90031-9).
  El modelo de impedancia de un parámetro (resistividad de flujo) que evalúa
  el efecto de suelo.
- Kephalopoulos, S., Paviotti, M., & Anfosso-Lédée, F. (2012). *Common noise
  assessment methods in Europe (CNOSSOS-EU)* (EUR 25379 EN). Oficina de
  Publicaciones de la Unión Europea.
  [doi:10.2788/31776](https://doi.org/10.2788/31776),
  [repositorio del JRC](https://publications.jrc.ec.europa.eu/repository/handle/JRC72550).
  Las clases de suelo por resistividad de flujo `"A"`-`"H"` que acepta
  `ground_effect_adjustment`.

## Normas

ECAC Doc 32, 1ª ed. (contornos de ruido de rotorcraft); guía de
modelado NORAH2 (EASA.2020.FC.06 SC01.D1.5d) §A.3-A.4: el hemisferio de ruido, el
ensanchamiento esférico, la atenuación atmosférica (ISO 9613-1, Tabla 4) y el
efecto de suelo de Chien-Soroka (impedancia de Delany-Bazley, resistividad de
flujo CNOSSOS). La integración sobre la trayectoria (SEL/LAmax/EPNL), los
contornos en malla de tierra y el apantallamiento del terreno son un desarrollo
posterior aparte.

## Véase también

- Referencia de la API: [`aircraft.rotorcraft_noise`](/phonometry/es/reference/api/aeroacoustics/rotorcraft-noise/).
