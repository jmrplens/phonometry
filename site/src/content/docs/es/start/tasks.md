---
title: "¿Qué necesitas medir?"
description: "La puerta de entrada a las guías con forma de tarea: el trabajo a la izquierda, la guía que lo responde a la derecha, con la norma que implementa."
---

El resto de este sitio está organizado por materias, que es lo correcto una vez
sabes qué materia se ocupa de tu problema y no sirve de nada antes. Esta página
va al revés: el trabajo a la izquierda, la guía que lo responde a la derecha, y
la norma que implementa esa guía para que puedas saber antes de hacer clic si
es la que aceptarán tu cliente, quien te revise o el organismo que te regula.

Si tu trabajo no está en la lista, [Todas las
guías](/es/start/guides/) es el inventario completo, y el
[glosario](/es/reference/glossary/) recorre otra vez el camino
contrario: tienes un símbolo sacado de un informe y quieres la guía que lo
calcula.

## A partir de una grabación

| El trabajo | Dónde se responde |
|---|---|
| Tengo una grabación WAV y necesito niveles ponderados A, $L_\mathrm{Aeq}$ y los niveles percentiles | [Construye un sonómetro](/es/signals/sound-level-meter/): IEC 61672-1 e IEC 61260-1, la cadena entera en una página ejecutable, del tono de calibrador a la comprobación de clase de cada etapa |
| Mis números no están en pascales y no sé qué son | [Calibración y dBFS](/es/signals/metrology/calibration/): el tono de calibrador, la sensibilidad en pascales por unidad digital, la regla de deriva antes/después y la alternativa digital en dBFS |
| Mi archivo es el WAV del propio sonómetro: 24 bits, multicanal, o un RF64 nocturno, y quiero leerlo y escribirlo sin tocar el nivel | [Leer y escribir audio de medición](/es/io/audio-files/): el `Signal` calibrado, la procedencia `bext`, el flujo por bloques, la escritura BWF y el sidecar de calibración |
| Necesito un espectro en lugar de un nivel | [Bancos de filtros](/es/signals/filters/filter-banks/) para niveles de banda (IEC 61260-1), [Análisis espectral](/es/signals/spectra/spectral-analysis/) para una estimación de densidad |

## Salas y edificación

| El trabajo | Dónde se responde |
|---|---|
| El tiempo de reverberación de una sala en la que puedo entrar | [Medición de la respuesta al impulso](/es/buildings/rooms/room-impulse-response/) para la adquisición (barridos de ISO 18233 y la alternativa del ruido interrumpido), y después [Acústica de salas](/es/buildings/rooms/room-acoustics/) para $T_{20}$, $T_{30}$, EDT, $C_{50}$, $C_{80}$ y el resto de ISO 3382-1 |
| El tiempo de reverberación de una sala que todavía no existe | [Predicción del tiempo de reverberación](/es/buildings/rooms/reverberation-prediction/): la familia de Sabine, con el apartado que dice qué modelo usar y cuándo fallan todos; [Absorción acústica en recintos](/es/buildings/rooms/enclosed-space-absorption/) cuando un informe de diseño tiene que citar EN 12354-6 |
| Si una sala está bastante silenciosa para lo que ocurre dentro | [Criterios de ruido de salas](/es/buildings/rooms/room-noise/): NC, RC Mark II y NR, y el apartado sobre cómo elegir entre ellos |
| El $R'_w$ o el $D_{\mathrm{n}T,\mathrm{w}}$ de un elemento separador que he medido en obra | [Medición del aislamiento en campo](/es/buildings/insulation/insulation-field/) (ISO 16283-1/-2) para la medición, y después [Índices globales de aislamiento](/es/buildings/insulation/insulation-ratings/) (ISO 717-1/-2) para el número único y los términos de adaptación |
| La prueba de que un muro cumple el CTE DB-HR | [Código Técnico de la Edificación](/es/buildings/insulation/spanish-building-code/): las magnitudes exigidas, contra cuál está escrita cada exigencia y la comprobación de cumplimiento |
| El aislamiento de un edificio que todavía estoy diseñando | [Predicción del aislamiento acústico (EN 12354)](/es/buildings/design/insulation-prediction/), y [Predicción detallada por bandas](/es/buildings/design/detailed-prediction/) cuando hay que desglosar las trayectorias por flancos |

## Máquinas, productos e instalaciones

| El trabajo | Dónde se responde |
|---|---|
| La potencia acústica de una máquina | [Potencia acústica](/es/devices/emission/sound-power/): empieza aquí sean cuales sean tus instalaciones: su apartado «Elegir un método» encamina hacia el método por presión (ISO 3744/3745/3746), en cámara reverberante (ISO 3741), por intensidad (ISO 9614) o por vibración superficial (ISO/TS 7849) |
| Un valor de emisión declarado para una hoja de características o un expediente CE | [Declarar la emisión sonora](/es/devices/emission/sound-power/#declarar-la-emision-sonora-iso-4871): ISO 4871, el nivel declarado ponderado A $L_{WAd}$ y su incertidumbre $K_{WA}$ |
| Cuánto van a atenuar un silenciador, un cerramiento o un tramo de conducto | [Silenciadores](/es/devices/noise-control/silencers/), [Control de ruido industrial](/es/devices/noise-control/noise-control/) para cerramientos y climatización, [Ruido por conductos](/es/devices/noise-control/duct-path/) |
| Un altavoz, un micrófono o un amplificador medidos según su norma | [Medidas electroacústicas](/es/devices/electroacoustics/electroacoustics/): IEC 60268-3/-4/-5 |
| La sonoridad de un programa en LUFS | [Sonoridad de programa y pico verdadero](/es/devices/broadcast/program-loudness/): ITU-R BS.1770-5 y EBU R 128 |

## Medio ambiente y transporte

| El trabajo | Dónde se responde |
|---|---|
| El $L_\mathrm{den}$, el $L_\mathrm{night}$ o un nivel de evaluación de un estudio ambiental | [Niveles ambientales](/es/environment/assessment/environmental-levels/): ISO 1996-1/-2, los indicadores y los ajustes que se les suman |
| La potencia de la fuente para un mapa de ruido viario o ferroviario | [Emisión de la fuente de tráfico viario CNOSSOS-EU](/es/environment/sources/cnossos-road-emission/) y [emisión de la fuente ferroviaria](/es/environment/sources/cnossos-rail-emission/): el anexo II de la 2002/49/CE, su lado de la fuente |
| El ruido de ensayo de tipo de un tren, una locomotora o un vagón | [Ruido del material rodante](/es/environment/sources/rolling-stock-noise/): la ISO 3095, sobre una vía juzgada por la EN 15610 y la EN 15461 |
| Cuánto quitan la distancia, una barrera o la meteorología | [Propagación en exteriores](/es/environment/propagation/outdoor-propagation/) (ISO 9613-2), [Efecto suelo y barreras](/es/environment/propagation/ground-barriers/), [Refracción atmosférica](/es/environment/propagation/atmospheric-refraction/) |
| Cuánto sonido devuelve una pantalla de carretera, medido donde está | [Reflexión acústica de una pantalla in situ](/es/environment/propagation/barrier-reflection/): EN 1793-5, el índice de reflexión acústica y $DL_{RI}$ |
| Si un parque eólico cumple | [Ruido de aerogeneradores](/es/environment/sources/wind-turbine-noise/): IEC 61400-11 y la evaluación de audibilidad tonal; [en la vivienda](/es/environment/sources/wind-turbine-receptor/): IEC TS 61400-11-2, la corrección por fondo, la valoración de la modulación de amplitud y el nivel de evaluación |
| El nivel de certificación del sobrevuelo de una aeronave | [Ruido de aeronaves: EPNL](/es/aircraft/aircraft-noise/): Anexo 16 de la OACI, y [Curvas de ruido de aeropuerto](/es/aircraft/airport-noise/) para el mapa alrededor del aeropuerto |

## Personas

| El trabajo | Dónde se responde |
|---|---|
| Si un trabajador supera el límite diario de exposición | [Exposición al ruido en el trabajo](/es/perception/hearing/occupational-exposure/): ISO 9612, el $L_\mathrm{EX,8h}$ y su incertidumbre |
| La sonoridad en sonios, o la agudeza, la aspereza y la intensidad de fluctuación | [Sonoridad](/es/perception/psychoacoustics/loudness/) (ISO 532-1/-2/-3), y después [Métricas de calidad sonora](/es/perception/psychoacoustics/sound-quality/) |
| Si un tono dentro de un ruido es audible, y en qué medida | [Audibilidad de tonos](/es/perception/psychoacoustics/tone-audibility/) (ISO/PAS 20065, DIN 45681) y [Tonos prominentes](/es/perception/psychoacoustics/tone-prominence/), cuyo apartado sobre qué métrica usar cubre las dos |
| El STI de un sistema de megafonía | [Índice de transmisión del habla](/es/perception/speech/speech-transmission/): IEC 60268-16, directo e indirecto (STIPA) |
| Un registro de vibración de asiento, de suelo o mano-brazo frente a la Directiva | [Vibración en humanos](/es/vibration/human/human-vibration/): ISO 2631-1 e ISO 5349-1, y [Vibración con choques múltiples](/es/vibration/human/multiple-shock-vibration/) para ISO 2631-5 |

## Materiales, y bajo el agua

| El trabajo | Dónde se responde |
|---|---|
| El coeficiente de absorción de una muestra | [Medida y clasificación de la absorción sonora](/es/materials/absorbers/absorption-measurement/) para la cámara reverberante (ISO 354, ISO 11654), [Tubo de impedancia](/es/materials/absorbers/impedance-tube/) para incidencia normal (ISO 10534-2) |
| La resistividad al flujo de aire o la rigidez dinámica de una capa | [Resistencia al flujo de aire](/es/materials/absorbers/airflow-resistance/) (ISO 9053-1/-2), [Rigidez dinámica](/es/materials/resilient/dynamic-stiffness/) (EN 29052-1) |
| Cuánto dispersa un difusor | [Difusores y dispersión](/es/materials/diffusers/diffusers/): ISO 17497-1/-2, y la diferencia entre los dos coeficientes |
| El ruido radiado por un buque, o la exposición de una campaña de hincado de pilotes | [Acústica submarina](/es/underwater/underwater-acoustics/) (ISO 17208, ISO 18406) y después [Exposición a ruido de mamíferos marinos](/es/underwater/marine-mammal-exposure/) |
| Hasta dónde llega un sonido en el mar | [Propagación submarina](/es/underwater/underwater-propagation/), y [Métodos numéricos de propagación submarina](/es/underwater/underwater-solvers/) cuando hace falta un campo dependiente de la distancia |

## Cuando hay más de un método válido

Varias guías llevan dentro la propia decisión, en un apartado escrito para quien
tiene el problema pero todavía no el método. Vale la pena abrirlas antes que la
guía que crees necesitar:

- [Elegir F, S o I](/es/signals/levels/time-weighting/#elegir-f-s-o-i): qué ponderación temporal exponencial pide una medición.
- [¿Qué arquitectura de filtro debería elegir?](/es/signals/filters/filter-gallery/#que-arquitectura-de-filtro-deberia-elegir): Butterworth frente a las cuatro alternativas, y a qué renuncia cada una.
- [Elegir un criterio: NC, RC Mark II o NR](/es/buildings/rooms/room-noise/#3-elegir-un-criterio-nc-rc-mark-ii-o-nr).
- [Elegir un modelo, y cuándo fallan todos](/es/buildings/rooms/reverberation-prediction/#4-elegir-un-modelo-y-cuando-fallan-todos): Sabine, Eyring, Millington, Fitzroy, Arau.
- [Elegir un método](/es/devices/emission/sound-power/#elegir-un-metodo): las siete rutas hacia la potencia acústica y cuál permite cada instalación.
- [Elegir un modelo de sonoridad](/es/perception/psychoacoustics/advanced-loudness/#elegir-un-modelo-de-sonoridad): Zwicker, Moore-Glasberg y Sottek.
- [Qué medida usar y cuándo](/es/perception/speech/objective-intelligibility/#4-que-medida-usar-y-cuando): el STI frente a las medidas intrusivas y no intrusivas.
- [Qué métrica de tonalidad usar y cuándo](/es/perception/psychoacoustics/tone-prominence/#3-que-metrica-de-tonalidad-usar-y-cuando).
- [¿Directo o indirecto?](/es/perception/speech/speech-transmission/#directo-o-indirecto-como-elegir): el STI de matriz completa frente a STIPA.
- [Elegir modelo](/es/underwater/underwater-solvers/#6-elegir-modelo): modos normales, rayos, haces gaussianos y ecuación parabólica.

## Antes de medir nada

Dos costumbres salvan más mediciones que ninguna de las páginas de arriba. Graba
el tono de calibrador por la misma cadena, antes y después, y toma la diferencia
como tu cota de deriva. [Primeros
pasos](/es/start/getting-started/) enseña por qué un nivel sin
calibrar no es aproximadamente correcto, sino arbitrario. Y lee el bloque «Qué
cubre esta guía» del final de la guía en la que aterrices: dice qué apartados,
anexos y métodos están implementados y cuáles no, que es lo primero por lo que
va a preguntar quien revise.
