---
title: "Erratas de Cox & D'Antonio (2017)"
description: "Erratas de Cox & D'Antonio (2017): 3 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 3 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre Cox & D'Antonio (2017), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Cox & D'Antonio, Acoustic Absorbers and Diffusers 3e (2017), Apéndice D (dos filas que la tabla no sabe distinguir)

- **Localización:** Apéndice D, «Random incidence scattering coefficient
  table», el grupo «Pyramids [6]», en las páginas impresas 499 y 500 (PDF 556
  y 557). Fuente no normativa: un libro de texto.
- **Lo impreso:** el grupo tiene cuatro filas. La página impresa 499 trae
  «$h = 30.5$ cm, $L = b = 2h$» y a continuación la misma descripción otra vez,
  con la línea de continuación «One in four pyramid corners raised from
  baseplate» debajo. La página impresa 500 trae «$h = 30.5$ cm, $L = b = h$» y
  después, de nuevo, «$h = 30.5$ cm, $L = b = 2h$» con la misma línea de
  continuación debajo.
- **El problema:** la segunda fila y la cuarta se imprimen con la misma
  descripción, la misma línea de continuación y números distintos: 0,38 frente
  a 0,44 en 1 kHz, 0,74 frente a 0,76 en 2 kHz, y 1,00 frente a una raya en
  5 kHz. Nada de lo impreso junto a una de ellas la distingue de la otra, así
  que quien busque «las pirámides de 30,5 cm con una esquina de cada cuatro
  levantada» encuentra dos respuestas y ninguna forma de elegir. Una tabla de
  valores medidos tiene que identificar sus filas, y esta no lo hace.
- **Evidencia:** las dos páginas leídas a seis aumentos. Las etiquetas son
  carácter por carácter la misma, las líneas de continuación también, y los
  valores difieren en trece de las dieciocho bandas, y sólo coinciden en 100,
  125, 160, 200 y 4000 Hz. La estructura del propio
  bloque es lo que hace evidente la lectura: la tabla empareja una superficie
  sin modificar con su versión modificada, y la página impresa 499 empareja
  $L = b = 2h$ con la suya. La página impresa 500 abre con $L = b = h$, así que
  su segunda fila es donde le toca a la modificada de $L = b = h$, con lo que
  el «2h» impreso sería el defecto. Eso es una lectura del patrón y no algo que
  la página afirme, y la fuente a la que se acredita el grupo, Sharma y
  Bradley, *J. Acoust. Soc. Am.* 134(5), 4095 (2013), es un resumen de congreso
  de una página que esta biblioteca no ha leído, así que el registro anota lo
  que la página hace y no lo que debería haber dicho. Verificado en la página
  PDF 556 (página impresa 499) y en la página PDF 557 (página impresa 500) de
  Cox y D'Antonio (2017), *Acoustic Absorbers and Diffusers*, tercera edición.
- **Comportamiento de la biblioteca:** se guardan las dos filas, con la
  descripción y la línea de continuación tal como se imprimen. Sus claves
  llevan la página impresa, que es lo único que las separa, y
  `test_two_pyramid_rows_are_told_apart_only_by_the_page_they_sit_on` de
  [`tests/materials/diffusers/test_scattering_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/diffusers/test_scattering_catalogue.py)
  fija que sigan siendo dos filas con dos espectros.
- **Estado:** no reportado.

## Cox & D'Antonio, Acoustic Absorbers and Diffusers 3e (2017), Apéndice B (una anchura en centímetros que su propia geometría hace metros)

- **Localización:** Apéndice B, «Normalized diffusion coefficient table»,
  sección 1, la primera superficie de la serie de anchuras, en la página
  impresa 482 (PDF 539). Fuente no normativa: un libro de texto.
- **Lo impreso:** la sección se encabeza «Effect of changing diffuser
  periodicity and width. Semicylinder(s) non-absorbing surfaces, radius 0.3 m
  (1 cm flat section between each period)», y sus cinco superficies se listan
  como «1 period, 0.61 cm wide», «2 periods, 1.22 m wide», «4 cylinders,
  2.44 m wide», «6 periods, 3.66 m wide» y «12 periods, 7.32 m wide».
- **El problema:** la primera anchura está en centímetros y las otras cuatro en
  metros, y la serie se duplica: 0,61, 1,22, 2,44, y después 3,66 y 7,32, que
  son seis y doce veces la primera. Un periodo de la superficie que describe el
  encabezado es un semicilindro de radio $0,3$ m más la sección plana de $1$ cm,
  así que $2 \times 0,3 + 0,01 = 0,61$ m. Una anchura de 0,61 cm son seis
  milímetros, la centésima parte de lo que da la geometría del propio
  encabezado y la centésima parte de lo que pide el resto de la serie.
- **Evidencia:** la misma superficie se lista en la Tabla C.3 del apéndice
  siguiente, bajo un encabezado con la misma geometría, y allí dice «1 period,
  0.61 m wide». O sea que el libro imprime las dos grafías de una misma
  superficie con doce páginas de diferencia, y la métrica es la que sostiene su
  aritmética. Verificado en la página PDF 539 (página impresa 482) y en la
  página PDF 549 (página impresa 492) de Cox y D'Antonio (2017), *Acoustic
  Absorbers and Diffusers*, tercera edición, releyendo la unidad a seis
  aumentos en las dos páginas: el apéndice imprime «cm» y la Tabla C.3 imprime
  «m».
- **Consecuencia para las tablas del propio libro:** la descripción de una
  superficie y la de las tres filas que la llevan. Los números de al lado no
  se ven afectados, que es lo que hace el defecto fácil de pasar por alto y
  digno de registrarse: quien compare un semicilindro medido con esta fila
  estará comparando contra un dispositivo de 0,61 m diga lo que diga la
  etiqueta.
- **Comportamiento de la biblioteca:** la fila conserva la anchura tal como se
  imprime, porque un catálogo que la corrigiera por su cuenta estaría
  afirmando una lectura que la página no hace. Las tres filas de la superficie
  la llevan en su clave y
  `test_every_section_heading_is_kept_whole` de
  [`tests/materials/diffusers/test_diffusion_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/diffusers/test_diffusion_catalogue.py)
  fija que el encabezado con la geometría viaje con ellas, que es lo que
  permite a quien lea ver la contradicción.
- **Estado:** no reportado.

## Cox & D'Antonio, Acoustic Absorbers and Diffusers 3e (2017), Tabla 6.7 (seis porosidades impresas en tanto por ciento en una columna de fracciones)

- **Localización:** Tabla 6.7, «Effective flow resistivity values for ground
  surfaces and other parameters», la columna «Porosity», en las páginas
  impresas 200 y 201 (PDF 257 y 258). Fuente no normativa: un libro de texto.
- **Lo impreso:** la columna se encabeza «Porosity» y no dice su unidad,
  mientras la de al lado se encabeza «Water content (%)». Todas las
  porosidades que imprime son fracciones entre 0,15 y 1 («0.5–0.9» para la
  nieve, «0.24» para el campo deportivo, «0.44» para la arena fina, «0.34–1» y
  otras así para las hierbas ajustadas), salvo en seis filas: «Mineral layer
  beneath mixed deciduous forest» «36.5», «Humus on pine forest floor»
  «58.1», «Pine forest litter (6–7 cm thick)» «38.9», «Grass root layer in
  loamy sand» «48 ± 4», «Loamy sand» «37.5» y «Bare sandy plain» «26.9».
- **El problema:** una porosidad es la fracción de un volumen que está
  abierta, así que no puede pasar de 1, y estas seis son porcentajes impresos
  en una columna que no dice su unidad y que en todas las demás filas lleva
  fracciones. Leídas en la unidad de la propia columna son porosidades de 26,9
  a 58,1, que ningún material tiene; leídas como tanto por ciento son de 0,269
  a 0,581, que es lo que son suelos como estos. La página deja que quien lee
  averigüe cuál de las dos, y un programa que lea la columna tal como se
  imprime se queda con el valor imposible.
- **Evidencia:** verificado en la página PDF 257 (página impresa 200) y en la
  página PDF 258 (página impresa 201) de Cox y D'Antonio (2017), *Acoustic
  Absorbers and Diffusers*, tercera edición: el encabezado no imprime unidad,
  y las seis celdas imprimen los valores citados, la cuarta como «48 ± 4».
- **Comportamiento de la biblioteca:** en
  [`PUBLISHED_GROUND_SURFACES`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/ground_surfaces.py)
  las seis filas dejan vacío `GroundSurface.porosity`, que es una fracción de 0
  a 1, y guardan la celda como `misprinted`: `why_missing("porosity")` y el
  rechazo de `printed("porosity")` citan la cifra que imprime la página, con el
  ± 4, y dicen por qué no se sirve. La biblioteca no la convierte en 0,365 ni en
  las demás, porque la página no imprime la unidad que esa conversión daría
  por supuesta. Toda fila de catálogo comprueba al construirse que una
  porosidad es una fracción.
  `test_the_six_percent_porosities_of_cox_are_held_as_misprinted` y
  `test_why_a_per_cent_porosity_is_missing_quotes_the_page` de
  [`tests/io/test_catalogue_row_contract.py`](https://github.com/jmrplens/phonometry/blob/main/tests/io/test_catalogue_row_contract.py)
  fijan las seis.
- **Estado:** sin notificar.
