/**
 * The Spanish landing page's text (es/index.mdx), in the shape home.ts gives
 * both locales. The English text is home-en.ts: each landing page is dated by
 * its own language's module alone (site/date-sources.json).
 */
import { designations, domains, passingChecks, sources } from './conformance-stats.mjs';
import { DOI, FICHE_CODE, type HomeContent, SPECTRUM_CODE } from './home.ts';
import { apiPages, catalogueRows, fiches, guides, installCommand, pythonFloor, version } from './repo-stats.mjs';

export const es: HomeContent = {
	statsLabel: 'La biblioteca en cuatro cifras',
	stats: [
		{ value: String(passingChecks), label: 'comprobaciones de conformidad superadas', href: '/es/reference/conformance/' },
		{ value: String(designations), label: `designaciones normativas y ${sources} fuentes publicadas adicionales, sobre ${domains} dominios` },
		{ value: String(catalogueRows), label: 'filas de catálogo publicadas, cada una con la fuente de la que sale', href: '/es/reference/catalogues/' },
		{ value: String(fiches), label: 'fichas PDF con el formato de informe que define su norma', href: '/es/reference/reports/' },
	],
	what: {
		title: 'Qué es',
		body: [
			'phonometry (publicada como PyOctaveBand hasta la 3.0.0) es una biblioteca de Python para medición, análisis y predicción acústica. Le das una señal, un espectro medido o un conjunto de datos geométricos y de materiales, y te devuelve la magnitud que define la norma, con los términos intermedios a la vista.',
			'Cada resultado es un dataclass tipado y congelado (<code>frozen</code>). Conserva los datos de entrada con los que se calculó, dibuja su propia figura con un <code>.plot()</code> de una línea en inglés o en español y, cuando una norma define un formato de informe, genera una ficha PDF de una página con <code>.report()</code>.',
			`La escribe y la mantiene una sola persona, se publica en <a href="https://pypi.org/project/phonometry/">PyPI</a> con licencia MIT (las tablas EASA ANP de ruido de aeronaves que incluye conservan los términos propios de EASA), se archiva con <a href="https://doi.org/${DOI}">DOI en Zenodo</a> y va por la versión ${version}. Necesita Python ${pythonFloor} o posterior con NumPy y SciPy. Los extras opcionales añaden el resto: <code>[plot]</code> para las figuras, <code>[perf]</code> para acelerar la ponderación temporal de impulso, <code>[report]</code> para las fichas PDF, <code>[audio]</code> para los formatos de audio más allá del WAV sin comprimir, <code>[full]</code> para los cuatro, y <code>[torch]</code>, fuera de <code>[full]</code>, para calcular las simulaciones FDTD con PyTorch.`,
		],
	},
	who: {
		title: 'Para quién es',
		items: [
			'Consultores y laboratorios de ensayo que necesitan el número que define la norma y los términos que hay detrás, en una forma que se pueda llevar a un informe.',
			'Investigadores que necesitan una implementación de referencia legible y citable en lugar de una caja negra, y ver de qué apartado sale cada fórmula.',
			'Ingenieros de audio, firmware y producto que necesitan filtros y ponderaciones de clase 1, distorsión, sonoridad y métricas de habla dentro de sus propios bancos de ensayo.',
			'Estudiantes y docentes, porque cada guía enuncia la norma, la fórmula y las hipótesis antes del código.',
		],
	},
	honest: {
		title: 'Qué no es',
		items: [
			'No es un instrumento certificado. El informe de conformidad consiste en que la biblioteca comprueba su propia salida frente a valores publicados en las normas; no es una calibración acreditada por un tercero. Una medición con validez legal sigue necesitando equipo con aprobación de modelo.',
			'No es un sistema de adquisición de datos. Procesa los arrays y los archivos que le pases; no habla con tarjetas de sonido, micrófonos ni analizadores.',
			'No implementa por completo todas las normas que cita. Cada guía indica qué apartados, métodos y anexos cubre y cuáles no.',
		],
	},
	proof: {
		title: 'Cómo se ve en uso',
		lead: 'Dos cosas que hace la biblioteca, difíciles de afirmar y fáciles de enseñar: el resultado de un análisis se dibuja solo y, cuando una norma prescribe un formato de informe, ese mismo resultado lo genera en PDF.',
		spectrum: {
			title: 'Un análisis y la figura que dibuja',
			note: 'Niveles por bandas de tercio de octava de una señal de dos tonos, con los límites de banda de IEC 61260-1 y la densidad espectral de potencia bruta al fondo. La figura de abajo es la que está publicada en la documentación, no una maqueta.',
			code: SPECTRUM_CODE,
			alt: 'Espectro en tercios de octava de una señal de dos tonos, con la densidad espectral de potencia bruta al fondo',
			caption: 'De la guía Primeros pasos: 33 bandas de 12,6 Hz a 20 kHz, con máximos en 100 Hz y 1 kHz.',
		},
		fiche: {
			title: 'Un índice global y la ficha que genera',
			note: 'El índice global de aislamiento a ruido aéreo de ISO 717-1 sobre las 16 bandas de tercio de octava que usa el índice, con el formato de un informe de laboratorio: cabecera de metadatos, tabla por bandas, la curva frente a la curva de referencia desplazada, el resultado de un solo número enmarcado y el veredicto frente al requisito. El código es la llamada que genera la ficha de al lado, con el bloque de metadatos reducido a los campos de los que se habla aquí.',
			code: FICHE_CODE,
			caption: 'Ficha del índice global a ruido aéreo (SoundReductionResult.report), Rw (C; Ctr).',
			linkTitle: 'Informe de ejemplo ISO 717-1 a ruido aéreo (PDF)',
			description:
				'Ficha de aislamiento a ruido aéreo de una página para un vidrio flotado de 6 mm: cabecera de metadatos, tabla de R en tercios de octava junto al gráfico de esa curva frente a la de referencia desplazada, el resultado Rw (C; Ctr) = 31 (-1; -3) dB enmarcado y el veredicto (PASS, en inglés como el resto de la ficha) frente al requisito de 30 dB.',
		},
	},
	coverage: {
		title: 'Qué abarca',
		lead: `Trece áreas de documentación sobre veintiún espacios de nombres de importación; en total, ${guides} guías y ${apiPages} páginas de referencia de la API. Cada fila enlaza al índice del área; las designaciones son las normas realmente implementadas ahí, no una lista de lecturas.`,
		headers: ['Área', 'Normas implementadas'],
		noStandard: 'sin norma que la rija',
		areas: [
			{
				name: 'Análisis de señal',
				href: '/es/signals/',
				summary: 'Bancos de filtros, ponderaciones, niveles, espectros, calibración e incertidumbre.',
				standards: ['IEC 61260-1', 'ANSI S1.11', 'IEC 61672-1', 'ISO 7196', 'IEC 61252', 'ISO 1996-1', 'IEC 60942', 'GUM'],
			},
			{
				name: 'Fluidos',
				href: '/es/fluids/',
				summary: 'El fluido por el que viaja el sonido, calculado a partir de las condiciones medidas: aire húmedo, agua de mar y gases ideales, cada uno con el modelo que lo produce.',
				standards: ['IEC 61094-2 Anexo F'],
			},
			{
				name: 'Sólidos elásticos',
				href: '/es/solids/',
				summary: 'Las constantes elásticas de un sólido y las tres velocidades longitudinales que se siguen de ellas, con las conversiones entre las formas que imprime una tabla.',
				standards: [],
			},
			{
				name: 'Archivos',
				href: '/es/io/',
				summary: 'Audio de medición de entrada y salida: lectura calibrada, procedencia, flujo por bloques, escritura BWF, conversión sin pérdidas; catálogos de materiales propios.',
				standards: ['EBU Tech 3285', 'ITU-R BS.2088'],
				keyword: 'audio de medición',
			},
			{
				name: 'Audición y percepción',
				href: '/es/perception/',
				summary: 'Sonoridad, calidad sonora, inteligibilidad del habla, audición y exposición.',
				standards: ['ISO 532-1/-2/-3', 'ECMA-418-1/-2', 'ISO 226', 'DIN 45692', 'IEC 60268-16', 'ANSI S3.5', 'DIN 45681', 'ISO/PAS 20065', 'ISO 7029', 'ISO 389-7', 'ISO 8253-1/-2', 'ISO 1999', 'ISO 9612', 'ISO 4869-1/-2/-3/-6'],
			},
			{
				name: 'Salas y edificación',
				href: '/es/buildings/',
				summary: 'Parámetros de sala, ruido de fondo, aislamiento en campo y laboratorio, predicción.',
				standards: ['ISO 3382-1/-2/-3', 'ISO 16283-1/-2/-3', 'ISO 10140', 'ISO 10848', 'ISO 15186-1/-2', 'ISO 16251-1', 'ISO 717-1/-2', 'EN 12354-1…-6', 'ISO 18233', 'ISO 12999-1', 'ISO 10052', 'ISO 16032', 'ANSI/ASA S12.2', 'ASTM E413'],
			},
			{
				name: 'Materiales y superficies',
				href: '/es/materials/',
				summary: 'Absorción, resistencia al flujo de aire, tubo de impedancia, modelos porosos y de metamaterial, difusores, dispersión.',
				standards: ['ISO 354', 'ISO 11654', 'ISO 10534-1/-2', 'ISO 9053-1/-2', 'ISO 17497-1/-2', 'ISO 13472-1/-2', 'EN 29052-1', 'ISO 12999-2'],
			},
			{
				name: 'Vibración y ruido estructural',
				href: '/es/vibration/',
				summary: 'Movilidad y FRF, aisladores, potencia radiada, uniones, vibración en humanos.',
				standards: ['ISO 7626-1/-2/-5', 'ISO 10846-1/-2/-3/-4/-5', 'ISO 9611', 'ISO/TS 7849-1/-2', 'EN 15657', 'EN 12354-5', 'ISO 2631-1/-2/-4/-5', 'ISO 5349-1/-2', 'ISO 8041-1/-2'],
			},
			{
				name: 'Medio ambiente y transporte',
				href: '/es/environment/',
				summary: 'Propagación en exteriores, barreras, refracción, indicadores ambientales, tráfico y aerogeneradores. De CNOSSOS-EU, la parte de fuentes del anexo II: el método de propagación de su apartado 2.5 no está implementado, y la atenuación en exteriores pasa aquí por ISO 9613-2 en su lugar.',
				standards: ['ISO 9613-1/-2', 'ISO 1996-1/-2', 'ISO/PAS 1996-3', 'NT ACOU 112', 'CNOSSOS-EU (Directiva 2002/49/CE, anexo II, 2.2 y 2.3)', 'IEC 61400-11'],
			},
			{
				name: 'Ruido de aeronaves',
				href: '/es/aircraft/',
				summary: 'Niveles de certificación, contornos de aeropuerto y el método de hemisferio para helicópteros.',
				standards: ['Anexo 16 OACI', 'IEC 61265', 'SAE ARP 866A/5534', 'ECAC Doc 29', 'ECAC Doc 32'],
			},
			{
				name: 'Acústica submarina',
				href: '/es/underwater/',
				summary: 'Niveles re 1 µPa, ruido radiado por buques, hincado de pilotes, ruido ambiente, pérdidas por transmisión.',
				standards: ['ISO 18405', 'ISO 17208-1/-2', 'ISO 18406', 'JOMOPANS-ECHO'],
			},
			{
				name: 'Fuentes y dispositivos',
				href: '/es/devices/',
				summary: 'Potencia acústica, intensidad, declaraciones de emisión, electroacústica, sonoridad de programa.',
				standards: ['ISO 3741', 'ISO 3744/3746', 'ISO 3745', 'ISO 9614-1/-2/-3', 'IEC 61043', 'ISO 4871', 'IEC 60268-3/-4/-5', 'ITU-R BS.1770-5', 'EBU R 128'],
			},
			{
				name: 'Simulación de ondas',
				href: '/es/simulation/',
				summary: 'Simulación FDTD 2D determinista, acústica y elástica P-SV, validada frente a oráculos analíticos y no frente a una norma.',
				standards: [],
			},
		],
	},
	start: {
		title: 'Empezar desde cero',
		lead: 'Tres pasos, en orden. Los dos primeros son cuestión de minutos; al tercero vuelves una y otra vez.',
		steps: [
			{
				title: 'Instálala',
				body: `Python ${pythonFloor} o posterior. La instalación básica trae NumPy y SciPy; el extra [full] añade cuatro más, [plot] para las figuras, [perf] para la ponderación temporal de impulso acelerada, [report] para las fichas PDF y [audio] para los formatos de audio más allá del WAV sin comprimir. [torch], que [full] deja fuera, calcula las simulaciones FDTD con PyTorch. En Windows y Linux de 32 bits, donde [full] no tiene soporte, [plot,report,audio] instala los otros tres. Si ya tienes instalada phonometry 3.x, actualízala con pip install -U phonometry y los extras que uses: la 3.x organiza sus imports de otra manera, y en ella from phonometry import filters falla.`,
				code: installCommand,
				href: '/es/start/getting-started/',
				linkText: 'Opciones de instalación',
			},
			{
				title: 'Haz un análisis de principio a fin',
				body: 'La guía Primeros pasos recorre una vez toda la cadena de proceso, primero con una señal sintética y después con un archivo WAV: calibración, ponderación frecuencial, banco de filtros, ponderación temporal y los niveles que salen.',
				href: '/es/start/getting-started/',
				linkText: 'Primeros pasos',
			},
			{
				title: 'Ve a tu dominio',
				body: 'Cada guía empieza por la norma que implementa, las magnitudes que define y las hipótesis, y sigue con el código y la figura. Cuando necesites la firma exacta, la referencia de la API tiene una página por módulo.',
				href: '/es/reference/api/',
				linkText: 'Referencia de la API',
			},
		],
	},
};
