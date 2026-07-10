---
title: "Informe de conformidad"
description: "El informe numérico de conformidad autogenerado: cada comprobación fija el valor esperado de una cláusula de norma frente al valor que calcula la librería, regenerado y exigido en CI."
---

El activo diferencial de phonometry no es la lista de funcionalidades sino la
prueba que hay detrás: cada métrica se implementa a partir del texto de la
norma que la rige, y un **informe numérico de conformidad** fija cada
comprobación a una norma, una cláusula o tabla, el valor esperado normativo y
el valor que la librería calcula realmente, con la desviación y un veredicto
de pasa/no pasa.

El informe es un documento autogenerado que la CI regenera en **cada pull
request** — la build falla si se desincroniza del código — de modo que siempre
está en sincronía con la librería publicada:

**[Lee el informe de conformidad completo (CONFORMANCE.md en GitHub)](https://github.com/jmrplens/phonometry/blob/main/docs/CONFORMANCE.md)**

## Qué contiene

- **Clases de filtro** — el veredicto de clase IEC 61260-1:2014 por
  arquitectura de filtro, con la atenuación relativa medida en la banda
  *determinante*, el límite de clase 1 que debe superar y el margen en dB.
- **Ponderaciones frecuenciales** — desviaciones de A/C (IEC 61672-1 Tabla 3)
  y G (ISO 7196 A.3) respecto a las curvas nominales, juzgadas en la
  frecuencia determinante con la banda de tolerancia aplicable y el margen.
- **Una tabla de conformidad por dominio** (niveles, psicoacústica, acústica
  de salas y de la edificación, potencia sonora, materiales, vibración,
  incertidumbre, ...): `Norma | Magnitud | Esperado | Calculado | Delta |
  Estado`, donde los valores esperados provienen de los ejemplos resueltos de
  las propias normas o de expresiones en forma cerrada sintetizadas a un resultado
  conocido.

## Cómo se genera

El registro de comprobaciones vive en
[`scripts/conformance_report.py`](https://github.com/jmrplens/phonometry/blob/main/scripts/conformance_report.py)
y se ejecuta en local con `make conformance`. Los valores esperados se toman
de las mismas tablas de referencia que exige la batería de tests, de modo que
el informe y los tests no pueden discrepar en silencio.

Para la filosofía de diseño detrás de este enfoque — y un caso de estudio
sobre la ponderación temporal de IEC 61672-1 — consulta
[Por qué phonometry](/phonometry/es/reference/why-phonometry/).
