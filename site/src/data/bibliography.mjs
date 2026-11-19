/**
 * What the bibliography page says of the works the pages cite that no
 * frontmatter says: which of its sections each work sits in, and, for the works
 * that have one, a note on why the work matters, in each language.
 *
 * The entries themselves are not here. Every work a page cites gets one, with
 * its citation and the pages that cite it, from the pages' own references
 * (src/lib/bibliography-entries.mjs); a work with nothing here sits in the
 * section most of its citing pages belong to (`BIBLIOGRAPHY_PREFIXES`), with no
 * note. A key here is the work's fragment on the English bibliography, the
 * `@id` the structured data gives it (src/lib/citations.mjs, `referenceId`),
 * and the Spanish page reads the same key for the same work, whatever its
 * Spanish fragment. A key that names a work no page cites stops the build, so
 * a note cannot outlive its work.
 */

/**
 * The sections of the page, in its order, each by the key its marker names
 * (`<!-- bibliography: signal-analysis -->`). The key is the English heading's
 * anchor; the headings and the prose under them are the page's own.
 */
export const BIBLIOGRAPHY_SECTIONS = Object.freeze(
  [
    'general-acoustics',
    'signal-analysis',
    'files',
    'hearing-and-perception',
    'rooms-and-buildings',
    'materials-and-surfaces',
    'vibration-and-structure-borne-sound',
    'environment-and-transport',
    'aircraft-noise',
    'underwater-acoustics',
    'sources-and-devices',
    'wave-simulation',
    'metrology',
  ].map((key) => Object.freeze({ key })),
);

/**
 * Where a work with no section of its own goes: the section of the route
 * prefix most of its citing pages fall under, the longest prefix winning. The
 * areas map to their sections, the theory pages to the section of their area,
 * and the metrology guides to Metrology. A catalogue page or the fluids guide
 * votes for nothing, so a work only they cite goes to General acoustics, the
 * first section.
 */
export const BIBLIOGRAPHY_PREFIXES = Object.freeze(
  [
    ['signals', 'signal-analysis'],
    ['signals/metrology', 'metrology'],
    ['io', 'files'],
    ['perception', 'hearing-and-perception'],
    ['buildings', 'rooms-and-buildings'],
    ['materials', 'materials-and-surfaces'],
    ['vibration', 'vibration-and-structure-borne-sound'],
    ['environment', 'environment-and-transport'],
    ['aircraft', 'aircraft-noise'],
    ['underwater', 'underwater-acoustics'],
    ['devices', 'sources-and-devices'],
    ['simulation', 'wave-simulation'],
    ['reference/theory/signal-analysis', 'signal-analysis'],
    ['reference/theory/perception', 'hearing-and-perception'],
    ['reference/theory/rooms-buildings', 'rooms-and-buildings'],
    ['reference/theory/materials-surfaces', 'materials-and-surfaces'],
    ['reference/theory/environment-transport', 'environment-and-transport'],
    ['reference/theory/vibration', 'vibration-and-structure-borne-sound'],
  ].map((pair) => Object.freeze(pair)),
);

/**
 * Each work's section and note, by its fragment on the English bibliography.
 * A note is Markdown, as the page's prose is, and the Spanish one is the
 * English one's twin.
 *
 * @type {Readonly<Record<string, Readonly<{section?: string, note?: Readonly<{en?: string, es?: string}>}>>>}
 */
export const BIBLIOGRAPHY_WORKS = Object.freeze({
  "book-kinsler-2000-fundamentals-of-acoustics": Object.freeze({
    section: "general-acoustics",
    note: Object.freeze({
      en: "ISBN 978-0-471-84789-2. The standard first course in acoustics: plane and spherical waves, acoustic impedance and the level definitions assumed throughout the guides.",
      es: "ISBN 978-0-471-84789-2. El primer curso clásico de acústica: ondas planas y esféricas, impedancia acústica y las definiciones de nivel sobre las que se apoyan todas las guías.",
    }),
  }),
  "doi-10-1007-978-1-4939-0755-7": Object.freeze({
    section: "general-acoustics",
    note: Object.freeze({
      en: "ISBN 978-1-4939-0754-0. A one-volume survey of every domain this library touches, from room acoustics to psychoacoustics and underwater sound; the cross-domain reference of first resort.",
      es: "ISBN 978-1-4939-0754-0. Un panorama en un solo volumen de todos los dominios que toca esta biblioteca, desde la acústica de salas hasta la psicoacústica y el sonido submarino; la referencia transversal a la que acudir primero.",
    }),
  }),
  "doi-10-1016-c2011-0-05897-0": Object.freeze({
    section: "general-acoustics",
    note: Object.freeze({
      en: "ISBN 978-0-12-391421-7. Sound fields, radiation and electroacoustic transducers; supports the electroacoustics and sound-power material.",
      es: "ISBN 978-0-12-391421-7. Campos sonoros, radiación y transductores electroacústicos; sustenta el material de electroacústica y potencia acústica.",
    }),
  }),
  "book-beranek-2019-acoustics-sound-fields-transducers-and-vibration": Object.freeze({
    section: "general-acoustics",
    note: Object.freeze({
      en: "ISBN 978-0-12-815227-0. The edition the conformance report reads for the baffled-piston radiation impedance and directivity (Eqs. 13.117, 13.118, 4.151, 13.102, numbered as in the first edition), and the one whose Table 7.1 gives the Delany-Bazley amplitudes discussed in [Source properties that are not errata](/reference/errata/not-errata/).",
      es: "ISBN 978-0-12-815227-0. La edición en la que el informe de conformidad lee la impedancia de radiación y la directividad del pistón en pantalla (Ecs. 13.117, 13.118, 4.151, 13.102, con la misma numeración que en la primera edición), y aquella cuya Tabla 7.1 da las amplitudes de Delany-Bazley que trata [Propiedades de las fuentes que no son erratas](/es/reference/errata/not-errata/).",
    }),
  }),
  "doi-10-1201-9781351228152": Object.freeze({
    section: "general-acoustics",
    note: Object.freeze({
      en: "ISBN 978-1-4987-2405-0. The steady-state room relations (section 6.4, Eqs. 6.43-6.44) behind `steady_state_spl` and `room_constant`, the enclosure insertion loss of section 7.4.2 (Eqs. 7.103, 7.111) that is the library default enclosure model, and Appendix D, which collects the porous-material coefficient sets of Table D.1 and the layered-construction recursions (Eqs. D.91-D.99).",
      es: "ISBN 978-1-4987-2405-0. Las relaciones de recinto en régimen estacionario (apartado 6.4, Ecs. 6.43-6.44) que hay detrás de `steady_state_spl` y `room_constant`, la pérdida por inserción de cerramientos del apartado 7.4.2 (Ecs. 7.103, 7.111), que es el modelo de cerramiento por defecto de la biblioteca, y el apéndice D, que reúne los juegos de coeficientes de materiales porosos de la tabla D.1 y las recursiones de construcciones en capas (Ecs. D.91-D.99).",
    }),
  }),
  "doi-10-1017-cbo9781139163927": Object.freeze({
    section: "general-acoustics",
    note: Object.freeze({
      en: "The sound power models of section 4.6 (Table 4.5, Eqs. 4.53-4.56), the room-to-room power balance of section 4.9 (Eqs. 4.92-4.101), the enclosure design equation of section 4.10 (Eqs. 4.102-4.115), the plateau method for panel transmission loss of section 3.9 (Table 3.1), the higher-order acoustic modes of a rigid circular duct of section 7.2 (Table 7.1) and the worked problems 4.16, 4.18 and 4.21 with their printed octave-band answers.",
      es: "Los modelos de potencia acústica del apartado 4.6 (Tabla 4.5, Ecs. 4.53-4.56), el balance de potencia entre recintos del apartado 4.9 (Ecs. 4.92-4.101), la ecuación de diseño de cerramientos del apartado 4.10 (Ecs. 4.102-4.115), el método de la meseta para la pérdida de transmisión de paneles del apartado 3.9 (Tabla 3.1), los modos acústicos de orden superior de un conducto circular rígido del apartado 7.2 (Tabla 7.1) y los problemas resueltos 4.16, 4.18 y 4.21 con sus respuestas impresas por bandas de octava.",
    }),
  }),
  "doi-10-1002-9780470172568": Object.freeze({
    section: "general-acoustics",
    note: Object.freeze({
      en: "ISBN 978-0-471-44942-3. The companion treatment of ducts, silencers and enclosures, and the handbook this library reads its commercial damping materials from: Table 14.1 of chapter 14, \"Structural Damping\", by Eric E. Ungar and Jeffrey A. Zapfe, which is the only table in the corpus that gives a loss factor with the temperature and the frequency at which it peaks.",
      es: "ISBN 978-0-471-44942-3. El tratamiento complementario de los conductos, los silenciadores y los cerramientos, y el manual del que esta biblioteca lee sus materiales de amortiguamiento comerciales: la Tabla 14.1 del capítulo 14, «Structural Damping», de Eric E. Ungar y Jeffrey A. Zapfe, que es la única tabla del corpus que da un factor de pérdidas con la temperatura y la frecuencia a las que alcanza su máximo.",
    }),
  }),
  "book-oppenheim-2010-discrete-time-signal-processing": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "ISBN 978-0-13-198842-2. The digital-filter theory behind the SOS cascades, the bilinear transform and the multirate decimation used by the filter banks.",
      es: "ISBN 978-0-13-198842-2. La teoría de filtros digitales que sustenta las cascadas SOS, la transformada bilineal y el diezmado multitasa que usan los bancos de filtros.",
    }),
  }),
  "web-smith-nd-introduction-to-digital-filters-with-audio-applications": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "Free companion treatment of digital-filter design and analysis, a good next step after the filter-bank guides.",
      es: "Tratamiento gratuito y complementario del diseño y análisis de filtros digitales, el paso natural tras las guías de bancos de filtros.",
    }),
  }),
  "web-bristow-johnson-2021-audio-eq-cookbook": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The biquad coefficient recipes (peaking, shelves, low/high-pass, band-pass, notch, all-pass) and their Q / bandwidth / shelf-slope parameterization, implemented verbatim by `ParametricEQ`.",
      es: "Las recetas de coeficientes biquad (pico, shelving, paso bajo y paso alto, paso banda, banda eliminada, paso todo) y su parametrización por Q / ancho de banda / pendiente de shelving, implementadas al pie de la letra por `ParametricEQ`.",
    }),
  }),
  "doi-10-1002-9781118032428": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "ISBN 978-0-470-24877-5. The reference for the Welch spectral estimators and their statistical quality, and for the multiple-input/output coherence functions of Chapter 7 (multiple and partial coherence, conditioned spectra) with the Section 9.3 error formulas implemented by `miso_coherence`. Also the correlation and time-delay formulas, the Hilbert-envelope chapter and the log-magnitude/phase Hilbert relation of the minimum-phase utilities.",
      es: "ISBN 978-0-470-24877-5. La referencia de los estimadores espectrales de Welch y su calidad estadística, y de las funciones de coherencia de sistemas de entradas múltiples del capítulo 7 (coherencia múltiple y parcial, espectros condicionados) con las fórmulas de error de la sección 9.3 que implementa `miso_coherence`. También las fórmulas de correlación y de retardo, el capítulo de la envolvente de Hilbert y la relación de Hilbert entre log-magnitud y fase de las utilidades de fase mínima.",
    }),
  }),
  "doi-10-1109-proc-1982-12433": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The multitaper method: Slepian tapers, eigenspectra and the adaptive weights implemented by `multitaper_psd`.",
      es: "El método multitaper: ventanas de Slepian, autoespectros propios y los pesos adaptativos que implementa `multitaper_psd`.",
    }),
  }),
  "doi-10-1017-cbo9780511622762": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "ISBN 978-0-521-43541-3. The multitaper development (Chapter 7) behind `multitaper_psd` and the Slepian-sequence eigenvalue tables that anchor its test oracle.",
      es: "ISBN 978-0-521-43541-3. El desarrollo multitaper (capítulo 7) tras `multitaper_psd` y las tablas de autovalores de las secuencias de Slepian que anclan su oráculo de test.",
    }),
  }),
  "std-iec-61260-1-2014": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The base-10 band edges and the class acceptance masks of the fractional octave banks.",
      es: "Los bordes de banda en base 10 y las máscaras de aceptación de clase de los bancos de fracción de octava.",
    }),
  }),
  "std-iec-61672-1-2013": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The A/C/Z weightings, the exponential time weightings and the level metrics of the sound level meter, with the tolerance tables used for verification.",
      es: "Las ponderaciones A/C/Z, las ponderaciones temporales exponenciales y las métricas de nivel del sonómetro, con las tablas de tolerancias usadas en la verificación.",
    }),
  }),
  "std-iec-61672-3-2013": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The periodic laboratory verification of a sound level meter.",
      es: "La verificación periódica de laboratorio de un sonómetro.",
    }),
  }),
  "std-iec-60942-2017": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The calibrator classes, level tolerances and the short-term stability criterion applied to calibration recordings.",
      es: "Las clases de calibrador, las tolerancias de nivel y el criterio de estabilidad a corto plazo aplicado a las grabaciones de calibración.",
    }),
  }),
  "std-iec-60268-4-2014": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The rated microphone characteristics: free-field sensitivity and its level re 1 V/Pa, the frequency response and the effective frequency range against the tolerance limits, the directional pattern and the directivity index, the overload sound pressure level, the equivalent sound pressure level due to inherent noise, and the rated impedances and power supply.",
      es: "Las características nominales del micrófono: sensibilidad en campo libre y su nivel re 1 V/Pa, la respuesta en frecuencia y el rango de frecuencias efectivo frente a los límites de tolerancia, el diagrama direccional y el índice de directividad, el nivel de presión acústica de sobrecarga, el nivel de presión acústica equivalente debido al ruido inherente, y las impedancias nominales y la alimentación.",
    }),
  }),
  "std-iec-60268-5-2003-a1-2007": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The rated loudspeaker characteristics: rated impedance, rated frequency range, characteristic sensitivity referred to 1 W at 1 m, the effective frequency range against the -10 dB band, the directivity index and the total harmonic distortion against frequency.",
      es: "Las características nominales del altavoz: impedancia nominal, rango de frecuencias nominal, sensibilidad característica referida a 1 W a 1 m, rango de frecuencias efectivo frente a la banda de -10 dB, índice de directividad y distorsión armónica total frente a la frecuencia.",
    }),
  }),
  "std-iec-60263-1982": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The scale proportions of the characteristic graphs: one frequency decade equal to 25 dB on the ordinate, and the polar diagram on a 25 dB reference-circle radius.",
      es: "Las proporciones de escala de las gráficas características: una década de frecuencia igual a 25 dB en la ordenada, y el diagrama polar sobre un radio de círculo de referencia de 25 dB.",
    }),
  }),
  "std-iec-60268-1-1985": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The simulated programme signal of Clause 7, and Appendix A: the quasi-peak network and meter of Table AI, Figure A1 and Tables AII and AIII, and the tone bursts of Clause A2, which start at the zero crossing of the tone with an integral number of full periods, repeat in trains at a stated repetition rate and last the burst durations of Table AII.",
      es: "La señal de programa simulado del capítulo 7, y el apéndice A: la red y el medidor de cuasipico de la tabla AI, la figura A1 y las tablas AII y AIII, y las ráfagas tonales del apartado A2, que comienzan en el paso por cero del tono con un número entero de periodos completos, se repiten en trenes a una tasa de repetición dada y duran lo que fija la tabla AII.",
    }),
  }),
  "doi-10-1109-proc-1978-10837": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The window figures of merit (Table 1): equivalent noise bandwidth, coherent gain, scalloping loss, worst-case processing loss, highest sidelobe level and main-lobe width, computed by `window_metrics` for any scipy taper.",
      es: "Las figuras de mérito de las ventanas (Tabla 1): ancho de banda de ruido equivalente, ganancia coherente, pérdida por festoneado, pérdida de proceso en el peor caso, nivel del lóbulo lateral más alto y anchura del lóbulo principal, calculadas por `window_metrics` para cualquier ventana de scipy.",
    }),
  }),
  "doi-10-1109-tau-1967-1161901": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The overlapped-segment variance formula behind the effective number of averages (Bendat & Piersol Section 11.5.2.2, Ref. 11).",
      es: "La fórmula de la varianza con segmentos solapados que hay detrás del número efectivo de promedios (Bendat y Piersol, apartado 11.5.2.2, Ref. 11).",
    }),
  }),
  "doi-10-1109-tassp-1976-1162830": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The GCC framework, the Table I weightings (Roth, SCOT, PHAT) and their conditions, and the maximum-likelihood (Hannan-Thomson) processor.",
      es: "El marco GCC, las ponderaciones de su Tabla I (Roth, SCOT, PHAT) y las condiciones de cada una, y el procesador de máxima verosimilitud (Hannan-Thomson).",
    }),
  }),
  "doi-10-1016-0888-3270-87-90085-9": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The comb-filter model of synchronous averaging (Eq. 8, with the unit height of its teeth in Eq. 9), the revised finite-record model that yields an exactly periodic result, and the observation that a non-harmonic interfering order is best rejected by choosing the number of averages so that a comb node lands on it, not by the habitual power of two.",
      es: "El modelo de filtro peine del promediado síncrono (Ec. 8, con la altura unidad de sus dientes en la Ec. 9), el modelo revisado de registro finito que da un resultado exactamente periódico, y la observación de que un orden interferente no armónico se rechaza mejor eligiendo el número de promedios para que un nodo del peine caiga sobre él, y no con la potencia de dos de costumbre.",
    }),
  }),
  "doi-10-1109-tit-1961-1057620": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "The original construction of the complementary pairs of §1.",
      es: "La construcción original de los pares complementarios del apartado 1.",
    }),
  }),
  "doi-10-1007-978-0-387-30441-0": Object.freeze({
    section: "signal-analysis",
    note: Object.freeze({
      en: "Part I Chapter 6 (Xiang, Digital Sequences): the Golay recursion of §1, the complementary-autocorrelation identity of Eq. (2) and the frequency-domain recovery procedure of Eq. (4) and Fig. 2. ISBN 978-0-387-77698-9.",
      es: "Parte I, capítulo 6 (Xiang, *Digital Sequences*): la recursión de Golay del apartado 1, la identidad de autocorrelación complementaria de la Ec. (2) y el procedimiento de recuperación en el dominio de la frecuencia de la Ec. (4) y la Fig. 2. ISBN 978-0-387-77698-9.",
    }),
  }),
  "std-ebu-tech-3285": Object.freeze({
    section: "files",
    note: Object.freeze({
      en: "The `bext` chunk read and written field by field at its published offsets, including the version-2 loudness values.",
      es: "El chunk `bext` leído y escrito campo a campo en sus posiciones publicadas, incluidos los valores de sonoridad de la versión 2.",
    }),
  }),
  "std-recommendation-itu-r-bs-2088-2": Object.freeze({
    section: "files",
    note: Object.freeze({
      en: "The RF64/BW64 64-bit container an overnight recording promotes to, resolved through its `ds64` sizes.",
      es: "El contenedor de 64 bits RF64/BW64 al que se promociona una grabación nocturna, resuelto a través de sus tamaños `ds64`.",
    }),
  }),
  "std-rfc-9639": Object.freeze({
    section: "files",
    note: Object.freeze({
      en: "The lossless codec behind the FLAC archive route, and the reason a round trip can return bit-identical codes.",
      es: "El códec sin pérdidas tras la ruta de archivo FLAC, y la razón de que un viaje de ida y vuelta pueda devolver códigos idénticos al bit.",
    }),
  }),
  "article-lipshitz-1992-quantization-and-dither-a-theoretical-survey": Object.freeze({
    section: "files",
    note: Object.freeze({
      en: "Why the optional dither is triangular-PDF at one LSB and offered only at 16 bits.",
      es: "Por qué el dither opcional es triangular de un LSB y se ofrece solo a 16 bits.",
    }),
  }),
  "doi-10-1121-1-392224": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The modulation-transfer framework the Speech Transmission Index is built on.",
      es: "El marco de transferencia de modulación sobre el que se construye el índice de transmisión del habla.",
    }),
  }),
  "doi-10-1121-1-1916407": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The articulation-band experiments behind the band-importance function of the Speech Intelligibility Index.",
      es: "Los experimentos por bandas de articulación que sustentan la función de importancia de banda del índice de inteligibilidad del habla.",
    }),
  }),
  "doi-10-1109-tasl-2011-2114881": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "STOI: the shared one-third-octave front end, the normalisation and signal-to-distortion clipping, and the per-band envelope correlation the index averages.",
      es: "STOI: el frontal común de tercios de octava, la normalización y el recorte señal-distorsión, y la correlación de envolventes por banda que promedia el índice.",
    }),
  }),
  "doi-10-1109-icassp-2010-5495701": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The short conference version of STOI.",
      es: "La versión corta de congreso del STOI.",
    }),
  }),
  "doi-10-1109-taslp-2016-2585878": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "ESTOI: the row- and column-normalised short-time spectrogram and its spectral-correlation intermediate index.",
      es: "ESTOI: el espectrograma de tiempo corto normalizado por filas y columnas y su índice intermedio de correlación espectral.",
    }),
  }),
  "doi-10-1163-9789004252424": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The standard textbook on auditory perception; pages 76-77 give the Glasberg and Moore (1990) ERB_N auditory-filter bandwidth and the Cam (ERB_N number) frequency scale the loudness models are written on.",
      es: "El libro de texto de referencia sobre percepción auditiva; sus páginas 76-77 dan el ancho de banda del filtro auditivo ERB_N de Glasberg y Moore (1990) y la escala de frecuencia Cam (número ERB_N) sobre la que se escriben los modelos de sonoridad.",
    }),
  }),
  "doi-10-1121-1-1915637": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The original equal-loudness measurements whose 40-phon contour became the A-weighting curve.",
      es: "Las mediciones originales de igual sonoridad cuya línea isofónica de 40 fonios se convirtió en la curva de ponderación A.",
    }),
  }),
  "std-iso-226-2023": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The modern equal-loudness contours, successors of the Fletcher-Munson curves.",
      es: "Las líneas isofónicas modernas, sucesoras de las curvas de Fletcher y Munson.",
    }),
  }),
  "doi-10-1007-978-3-540-68888-4": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The psychoacoustic-annoyance model and the closed-form fluctuation strength for amplitude-modulated broadband noise.",
      es: "El modelo de molestia psicoacústica y la forma cerrada de la intensidad de fluctuación para ruido de banda ancha modulado en amplitud.",
    }),
  }),
  "doi-10-1121-2-0000410": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The fluctuation-strength signal model and its Table 1 literature values.",
      es: "El modelo de señal de la intensidad de fluctuación y sus valores de la Tabla 1 de la literatura.",
    }),
  }),
  "doi-10-5281-zenodo-7934709": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The open MATLAB reference used as the numeric oracle for the fluctuation-strength cross-checks.",
      es: "La referencia abierta en MATLAB usada como oráculo numérico de las comprobaciones de la intensidad de fluctuación.",
    }),
  }),
  "std-ecma-418-1-2024-3rd-ed": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The freely downloadable tone-to-noise ratio and prominence ratio methods.",
      es: "Los métodos de relación tono-ruido y relación de prominencia, de descarga gratuita.",
    }),
  }),
  "std-ecma-74-2025-22nd-ed": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The freely downloadable parent emission standard whose Annex D delegates tone assessment to ECMA-418-1.",
      es: "La norma de emisión matriz, de descarga gratuita, cuyo anexo D delega la evaluación de tonos en ECMA-418-1.",
    }),
  }),
  "std-iso-pas-20065-2016": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "Withdrawn and superseded by [ISO/TS 20065:2022](https://www.iso.org/standard/81518.html). The engineering method for the objective audibility of tones; the implementation follows the 2016 PAS edition.",
      es: "Anulada y sustituida por [ISO/TS 20065:2022](https://www.iso.org/standard/81518.html). El método de ingeniería para la audibilidad objetiva de tonos; la implementación sigue la edición PAS de 2016.",
    }),
  }),
  "std-iso-7029-2017": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The age model of the hearing threshold and its population spread.",
      es: "El modelo por edad del umbral de audición y su dispersión poblacional.",
    }),
  }),
  "std-iso-389-7-2005": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The audiometric zero as a sound pressure level.",
      es: "El cero audiométrico como nivel de presión acústica.",
    }),
  }),
  "std-iso-1999-2013": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The NIPTS model, its distribution and the HTLAN combination.",
      es: "El modelo de NIPTS, su distribución y la combinación HTLAN.",
    }),
  }),
  "doi-10-1121-1-1903482": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "A field study of the noise exposure-response relations later codified in ISO 1999.",
      es: "Un estudio de campo de las relaciones exposición-respuesta del ruido codificadas después en la ISO 1999.",
    }),
  }),
  "doi-10-26616-nioshpub98126": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The freely available criteria document behind the 85 dB(A) recommended exposure limit and the hearing-conservation and fence discussion.",
      es: "El documento de criterios de libre acceso que sustenta el límite de exposición recomendado de 85 dB(A) y la discusión de conservación auditiva y umbral.",
    }),
  }),
  "std-iso-9612-2009": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The three measurement strategies and the Annex C uncertainty budget.",
      es: "Las tres estrategias de medición y el balance de incertidumbre del anexo C.",
    }),
  }),
  "report-european-parliament-and-council-2003-directive-2003-10-ec-on-the-minimum-health-and-safety-requirements-regarding-the-exposure-of-workers-to-the-risks-arising-from-physical-agents-noise": Object.freeze({
    section: "hearing-and-perception",
    note: Object.freeze({
      en: "The EU exposure action and limit values for occupational noise.",
      es: "Los valores de exposición que dan lugar a una acción y el valor límite de la UE para el ruido laboral.",
    }),
  }),
  "doi-10-1016-c2012-0-03257-5": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The architectural-design companion to the measurement standards: the rectangular-room eigenfrequencies and the Morse/Pierce mode count (Chapter 8), the crowd self-noise of an occupied room (Chapter 17) and the gain-before-feedback criterion of a reinforcement system (Chapter 18).",
      es: "El complemento de diseño arquitectónico a las normas de medición: las frecuencias propias de la sala rectangular y el recuento de modos de Morse y Pierce (capítulo 8), el ruido autogenerado por los ocupantes de una sala (capítulo 17) y el criterio de ganancia antes de la realimentación de un sistema de refuerzo sonoro (capítulo 18).",
    }),
  }),
  "doi-10-1201-9781315372150": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The reference monograph on sound fields in rooms: statistical decay theory, the Schroeder frequency, absorption and the perceptual room parameters.",
      es: "La monografía de referencia sobre el campo sonoro en salas: la teoría estadística del decaimiento, la frecuencia de Schroeder, la absorción y los parámetros perceptivos de sala.",
    }),
  }),
  "book-sabine-1922-collected-papers-on-acoustics": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The founding reverberation experiments and the Sabine law.",
      es: "Los experimentos fundacionales de la reverberación y la ley de Sabine.",
    }),
  }),
  "doi-10-1121-1-1915175": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The mean-free-path reverberation formula for strongly absorbing rooms.",
      es: "La fórmula de reverberación por recorrido libre medio para salas muy absorbentes.",
    }),
  }),
  "doi-10-1121-1-1915588": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The per-surface logarithmic reverberation formula.",
      es: "La fórmula de reverberación logarítmica por superficie.",
    }),
  }),
  "doi-10-1121-1-1907814": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The axial reverberation formula for anisotropic absorption.",
      es: "La fórmula de reverberación axial para absorción anisótropa.",
    }),
  }),
  "article-arau-puchades-1988-an-improved-reverberation-formula": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The geometric-mean refinement of the axial reverberation formula.",
      es: "El refinamiento por media geométrica de la fórmula de reverberación axial.",
    }),
  }),
  "doi-10-1121-1-1909343": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The backward integration of the squared impulse response into a decay curve.",
      es: "La integración inversa de la respuesta al impulso al cuadrado en una curva de decaimiento.",
    }),
  }),
  "doi-10-3813-aaa-918574": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The impulse-to-noise-ratio (INR) analysis of decay-range requirements.",
      es: "El análisis de la relación impulso-ruido (INR) sobre los requisitos de rango de decaimiento.",
    }),
  }),
  "book-everest-2001-master-handbook-of-acoustics": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "ISBN 978-0-07-136097-5. A practical room-acoustics handbook; its Fig. 7-22 worked example anchors the reverberation-prediction conformance suite.",
      es: "ISBN 978-0-07-136097-5. Un manual práctico de acústica de salas; su ejemplo resuelto de la Fig. 7-22 ancla la batería de conformidad de la predicción de reverberación.",
    }),
  }),
  "book-carrion-isbert-1998-diseno-acustico-de-espacios-arquitectonicos": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "ISBN 978-84-8301-252-9. A Spanish-language textbook on acoustic room design.",
      es: "ISBN 978-84-8301-252-9. Un manual en español sobre el diseño acústico de salas.",
    }),
  }),
  "doi-10-1121-1-2369239": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The original NC curves and their speech-interference rationale.",
      es: "Las curvas NC originales y su razonamiento de interferencia con el habla.",
    }),
  }),
  "article-kosten-1962-community-reaction-criteria-for-external-noises": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "Published by Her Majesty's Stationery Office. The NR curve family contrasted with NC.",
      es: "Publicado por Her Majesty's Stationery Office. La familia de curvas NR que se contrasta con NC.",
    }),
  }),
  "doi-10-3397-1-2828446": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The RC Mark II procedure later codified by ANSI/ASA S12.2 Annex D.",
      es: "El procedimiento RC Mark II codificado después por el Anexo D de ANSI/ASA S12.2.",
    }),
  }),
  "std-iso-3382-1-2009": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "Room-parameter definitions, position requirements and just-noticeable differences.",
      es: "Las definiciones de parámetros de sala, los requisitos de posiciones y las diferencias apenas perceptibles.",
    }),
  }),
  "std-iso-3382-2-2008": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The accuracy grades and position counts of reverberation measurement.",
      es: "Los grados de exactitud y los recuentos de posiciones de la medición de la reverberación.",
    }),
  }),
  "std-iso-3382-3-2012": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "Since revised as [ISO 3382-3:2022](https://www.iso.org/standard/77437.html). The open-plan speech-privacy quantities.",
      es: "Revisada después como [ISO 3382-3:2022](https://www.iso.org/standard/77437.html). Las magnitudes de privacidad del habla en oficinas diáfanas.",
    }),
  }),
  "std-iso-18233-2006": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The swept-sine and MLS acquisition of impulse responses.",
      es: "La adquisición de respuestas al impulso por barrido sinusoidal y MLS.",
    }),
  }),
  "std-iso-354-2003": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The reverberation-room absorption measurement behind the surface data.",
      es: "La medición de absorción en cámara reverberante que sustenta los datos de superficie.",
    }),
  }),
  "std-en-12354-6-2003": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The absorption member of the EN 12354 prediction family.",
      es: "El miembro de absorción de la familia de predicción EN 12354.",
    }),
  }),
  "std-ansi-asa-s12-2-2019": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The normative NC tangency method and the RC Mark II rating of its informative Annex D, with its spectral tag.",
      es: "El método de tangencia NC normativo y la valoración RC Mark II de su Anexo D informativo, con su etiqueta espectral.",
    }),
  }),
  "doi-10-4324-9780080550473": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "ISBN 978-0-7506-6526-1. The comprehensive treatment of airborne and impact sound insulation: measurement chains, flanking transmission and the EN 12354 prediction framework.",
      es: "ISBN 978-0-7506-6526-1. El tratamiento exhaustivo del aislamiento a ruido aéreo y de impactos: las cadenas de medición, la transmisión por flancos y el marco de predicción EN 12354.",
    }),
  }),
  "doi-10-1201-9781482266016": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "ISBN 978-0-415-42853-8. A compact textbook on sound transmission in buildings, from single and double constructions to floating floors.",
      es: "ISBN 978-0-415-42853-8. Un manual compacto sobre la transmisión del sonido en edificios, de las construcciones simples y dobles a los suelos flotantes.",
    }),
  }),
  "book-harris-1977-manual-para-el-control-del-ruido": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "Instituto de Estudios de Administración Local. The Spanish translation of the first edition of the *Handbook of Noise Control* (McGraw-Hill, 1957), cited in this tree as Harris (1977). Chapter 19, \"Control del ruido a través de los sólidos\", by Fritz Ingerslev and Cyril M. Harris, prints in its Tables 19.2 to 19.4 the average improvement in impact sound insulation of twenty-three floor finishes, floating screeds and timber floors on a bare concrete floor, and Table 14.2, in Richard N. Hamme's chapter on vibration damping, the decay rate of eight asphalt felt treatments on a standard steel panel.",
      es: "Instituto de Estudios de Administración Local. La traducción española de la primera edición del *Handbook of Noise Control* (McGraw-Hill, 1957), citada en este árbol como Harris (1977). Su capítulo 19, «Control del ruido a través de los sólidos», de Fritz Ingerslev y Cyril M. Harris, imprime en las tablas 19.2 a 19.4 la mejora media del aislamiento al impacto de veintitrés acabados, soleras flotantes y suelos de madera sobre un forjado de hormigón desnudo, y la tabla 14.2, en el capítulo de Richard N. Hamme sobre el amortiguamiento de la vibración, la tasa de decaimiento de ocho tratamientos de fieltro asfáltico sobre un panel normalizado de acero.",
    }),
  }),
  "book-harris-1995-manual-de-medidas-acusticas-y-control-del-ruido": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "McGraw-Hill. The Spanish edition of the handbook, cited in this tree as Harris 3e and not to be confused with the window paper of F. J. Harris under Signal processing. Chapter 30 prints in Tables 30.2 and 30.3 the noise reduction coefficient of nineteen carpets on bare concrete and on a hair pad; Chapter 31 prints in seven tables the sound transmission class of stud walls, block walls, doors, sealed windows and floor-ceiling systems, and Chapter 32, \"Aislamiento del sonido transmitido por estructuras\", prints in its Tables 32.1 to 32.8 the measured impact insulation class of forty-two floor-ceiling constructions and the improvement six elastic surface treatments add over a hard massive floor.",
      es: "McGraw-Hill. La edición española del manual, citada en este árbol como Harris 3e y que no hay que confundir con el artículo de ventanas de F. J. Harris, en Análisis de señal. Su capítulo 30 imprime en las tablas 30.2 y 30.3 el coeficiente de reducción del ruido de diecinueve alfombras sobre hormigón desnudo y sobre un relleno de pelo; su capítulo 31 imprime en siete tablas la clase de transmisión del sonido de tabiques de montantes, muros de bloques, puertas, ventanas selladas y sistemas de suelo-techo, y su capítulo 32, «Aislamiento del sonido transmitido por estructuras», imprime en las tablas 32.1 a 32.8 la clase de aislamiento al impacto medida de cuarenta y dos conjuntos de suelo-techo y la mejora que seis tratamientos elásticos de superficie añaden sobre un suelo macizo.",
    }),
  }),
  "book-arau-puchades-1999-abc-de-la-acustica-arquitectonica": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "ISBN 84-329-2017-7. The Spanish textbook of architectural acoustics, cited in this tree as Arau-Puchades (1999) and not to be confused with his 1988 paper on the reverberation formula. Its Table 4.1 prints the density, the critical frequency of a one-centimetre plate and the damping factor of seventeen solids, and its Table 6.1 the octave-band absorption coefficients of building materials and finishes, each row numbered; the book prints a decimal point.",
      es: "ISBN 84-329-2017-7. El manual español de acústica arquitectónica, citado en este árbol como Arau-Puchades (1999) y que no hay que confundir con su artículo de 1988 sobre la fórmula de reverberación. Su tabla 4.1 imprime la densidad, la frecuencia crítica de una placa de un centímetro y el factor de amortiguamiento de diecisiete sólidos, y su tabla 6.1 los coeficientes de absorción por bandas de octava de materiales y acabados de construcción, con cada fila numerada; el libro imprime punto decimal.",
    }),
  }),
  "std-iso-717-1-2020": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The reference-curve rating and the spectrum adaptation terms C and Ctr.",
      es: "La valoración por curva de referencia y los términos de adaptación espectral C y Ctr.",
    }),
  }),
  "std-iso-16283-1-2014": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The field airborne measurement method.",
      es: "El método de medición aérea en campo.",
    }),
  }),
  "std-en-29052-1-1992-iso-9052-1-1989": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The resonance method for the dynamic stiffness per unit area, identical to EN 29052-1.",
      es: "El método de resonancia para la rigidez dinámica por unidad de superficie, idéntico a EN 29052-1.",
    }),
  }),
  "doi-10-1016-s0003-682x-98-00068-1": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The measurement behind the 50 mm rows of Hopkins' Table A4: butterfly 1.7 MN/m, double-triangle 16.1 MN/m and vertical-twist 94.0 MN/m.",
      es: "La medida que hay detrás de las filas de 50 mm de la Tabla A4 de Hopkins: mariposa 1,7 MN/m, doble triángulo 16,1 MN/m y torsión vertical 94,0 MN/m.",
    }),
  }),
  "doi-10-1007-978-3-030-51202-6": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The mirror-source model (Chapter 11), with the reflection-factor and delay expressions.",
      es: "El modelo de fuentes imagen (capítulo 11), con las expresiones del factor de reflexión y del retardo.",
    }),
  }),
  "doi-10-1121-1-382599": Object.freeze({
    section: "rooms-and-buildings",
    note: Object.freeze({
      en: "The reflection-count decomposition of the rectangular-room image lattice.",
      es: "La descomposición por número de reflexiones de la retícula de fuentes imagen de una sala rectangular.",
    }),
  }),
  "doi-10-1002-9780470747339": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "ISBN 978-0-470-74661-5. The porous-material theory linking airflow resistivity, surface impedance and absorption.",
      es: "ISBN 978-0-470-74661-5. La teoría del material poroso que enlaza resistividad al flujo, impedancia superficial y absorción.",
    }),
  }),
  "doi-10-1201-9781315369211": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "ISBN 978-1-4987-4099-9. The monograph on absorber and diffuser measurement and design, by the authors behind the ISO 17497-2 diffusion-coefficient method.",
      es: "ISBN 978-1-4987-4099-9. La monografía sobre medida y diseño de absorbentes y difusores, de los autores del método del coeficiente de difusión de ISO 17497-2.",
    }),
  }),
  "doi-10-1007-978-3-030-84300-7": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "Volume 143 of the series Topics in Applied Physics. An edited umbrella volume on resonant and periodic sound-absorbing and sound-diffusing structures, from the transfer-matrix and critical-coupling theory of metamaterial absorbers to deep-subwavelength diffusers; the modern metamaterials companion to Cox & D'Antonio.",
      es: "Volumen 143 de la serie Topics in Applied Physics. Un volumen editado que abarca las estructuras resonantes y periódicas que absorben y difunden el sonido, desde la teoría de la matriz de transferencia y el acoplamiento crítico de los absorbentes de metamaterial hasta los difusores de sublongitud de onda profunda; el complemento moderno sobre metamateriales de Cox & D'Antonio.",
    }),
  }),
  "doi-10-1121-1-1310192": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The free-field diffusion-coefficient method behind ISO 17497-2 and the published N = 7 QRD geometry of the worked example.",
      es: "El método del coeficiente de difusión en campo libre tras ISO 17497-2 y la geometría publicada del QRD N = 7 del ejemplo resuelto.",
    }),
  }),
  "std-aes-4id-2001": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "Printed in the *Journal of the Audio Engineering Society*, 49(3), 149-165. The single-plane free-field diffusion-coefficient procedure that ISO 17497-2 later standardised.",
      es: "Publicado en el *Journal of the Audio Engineering Society*, 49(3), 149-165. El procedimiento del coeficiente de difusión de plano único en campo libre que ISO 17497-2 normalizó después.",
    }),
  }),
  "doi-10-1038-s41598-017-05710-5": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The metadiffuser model: resonator-loaded slits reproducing Schroeder phase profiles and ternary sequences from deep-subwavelength panels.",
      es: "El modelo de metadifusor: ranuras cargadas con resonadores que reproducen perfiles de fase de Schroeder y secuencias ternarias con paneles en sublongitud de onda profunda.",
    }),
  }),
  "article-jimenez-2019-beyond-phase-grating-diffusers-using-locally-resonant-metamaterials": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The congress companion to the metadiffuser paper: the transfer-matrix chain and the slow-sound dispersion picture.",
      es: "El acompañante de congreso del artículo de los metadifusores: la cadena de matrices de transferencia y la imagen de dispersión de sonido lento.",
    }),
  }),
  "doi-10-3390-app7060618": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The slit + Helmholtz-resonator transfer-matrix model and the critical-coupling condition.",
      es: "El modelo por matrices de transferencia de la ranura con resonadores de Helmholtz y la condición de acoplamiento crítico.",
    }),
  }),
  "doi-10-1063-1-4962328": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The resonator impedance and radiation end corrections, and the published λ/88 perfect absorber.",
      es: "La impedancia del resonador y sus correcciones de radiación, y el absorbente perfecto de λ/88 publicado.",
    }),
  }),
  "doi-10-1121-1-400379": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The visco-thermal effective parameters of the slit and the square necks and cavities.",
      es: "Los parámetros efectivos viscotérmicos de la ranura y de los cuellos y cavidades cuadrados.",
    }),
  }),
  "std-iso-10534-2-1998": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "Adopted in Europe as EN ISO 10534-2:2001, and since revised as [ISO 10534-2:2023](https://www.iso.org/standard/81294.html). The two-microphone transfer-function method and its plane-wave limits.",
      es: "Adoptada en Europa como EN ISO 10534-2:2001, y revisada después como [ISO 10534-2:2023](https://www.iso.org/standard/81294.html). El método de la función de transferencia con dos micrófonos y sus límites de onda plana.",
    }),
  }),
  "std-astm-e2611-19": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The edition the library implements, since revised as [ASTM E2611-24](https://store.astm.org/e2611-24.html). The four-microphone transfer-matrix transmission-loss method.",
      es: "La edición que implementa la biblioteca, revisada después como [ASTM E2611-24](https://store.astm.org/e2611-24.html). El método de pérdida por transmisión por matriz de transferencia con cuatro micrófonos.",
    }),
  }),
  "std-iso-9053-1-2018": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The static airflow-resistance method and its reference velocity.",
      es: "El método estático de resistencia al flujo de aire y su velocidad de referencia.",
    }),
  }),
  "std-iso-9053-2-2020": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The alternating airflow-resistance method with the Annex A effective ratio of specific heats.",
      es: "El método alterno de resistencia al flujo de aire con la relación efectiva de calores específicos del Anexo A.",
    }),
  }),
  "std-iso-10534-1-1996": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "Implemented as its European adoption, BS EN ISO 10534-1:2001. The standing-wave-ratio method.",
      es: "Implementada como su adopción europea, BS EN ISO 10534-1:2001. El método de la razón de onda estacionaria.",
    }),
  }),
  "std-iso-11654-1997": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The weighted sound-absorption rating $\\alpha_\\mathrm{w}$, its shape indicators and the absorption class.",
      es: "La valoración ponderada de absorción acústica $\\alpha_\\mathrm{w}$, sus indicadores de forma y la clase de absorción.",
    }),
  }),
  "std-iso-12999-2-2020": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The reproducibility and repeatability uncertainties of the reverberation-room quantities and their single-number ratings.",
      es: "Las incertidumbres de reproducibilidad y repetibilidad de las magnitudes de cámara reverberante y de sus valoraciones de número único.",
    }),
  }),
  "std-iso-17497-1-2004-a1-2014": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The edition the library implements. The turntable scattering-coefficient method.",
      es: "La edición que implementa la biblioteca. El método del coeficiente de dispersión con mesa giratoria.",
    }),
  }),
  "std-iso-17497-2-2012": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The goniometer diffusion-coefficient method.",
      es: "El método del coeficiente de difusión con goniómetro.",
    }),
  }),
  "std-iso-13472-1-2002": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The edition the library implements, since revised as ISO 13472-1:2022. The subtraction technique with the Adrienne window and the sampled-area radius.",
      es: "La edición que implementa la biblioteca, revisada después como ISO 13472-1:2022. La técnica de sustracción con la ventana de Adrienne y el radio de área muestreada.",
    }),
  }),
  "std-iso-13472-2-2010": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The edition the library implements, since revised as ISO 13472-2:2025. The spot-tube method and its plane-wave and spacing limits.",
      es: "La edición que implementa la biblioteca, revisada después como ISO 13472-2:2025. El método de tubo puntual y sus límites de onda plana y de espaciado.",
    }),
  }),
  "doi-10-1121-1-423870": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The exact MPP impedance (Eq. 2), end corrections, design formulas and the Fig. 5 example pinned in the tests.",
      es: "La impedancia exacta del panel microperforado (Ec. 2), las correcciones de extremo, las fórmulas de diseño y el ejemplo de la Fig. 5 fijado en los tests.",
    }),
  }),
  "doi-10-3813-aaa-919183": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The critical-coupling condition applied to a rigidly-backed layer of ordinary high-porosity absorber, connecting the porous-material models of the characterisation section to perfect single-frequency absorption.",
      es: "La condición de acoplamiento crítico aplicada a una capa de absorbente corriente de alta porosidad con fondo rígido, que conecta los modelos de material poroso del apartado de caracterización con la absorción perfecta a una sola frecuencia.",
    }),
  }),
  "doi-10-1007-978-3-540-76833-3": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "ISBN 978-3-540-76832-6. Sections D.3-D.6 (layer reflection, multilayer scheme, diffuse-field integrals) and G.11 (empirical porous relations).",
      es: "ISBN 978-3-540-76832-6. Apartados D.3-D.6 (reflexión en una capa, esquema multicapa, integrales de campo difuso) y G.11 (relaciones porosas empíricas).",
    }),
  }),
  "doi-10-1016-0003-682x-70-90031-9": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The original one-parameter empirical model for fibrous absorbers: the relations in frequency over flow resistivity, with their stated range of validity. The same model is the one-parameter flow-resistivity ground-impedance model.",
      es: "El modelo empírico original de un parámetro para absorbentes fibrosos: las relaciones en función de la frecuencia dividida por la resistividad al flujo, con su rango de validez declarado. El mismo modelo es el modelo de impedancia del suelo de un parámetro (resistividad de flujo).",
    }),
  }),
  "doi-10-1250-ast-11-19": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The positive-real regression implemented in miki.",
      es: "La regresión de parte real positiva que implementa miki.",
    }),
  }),
  "doi-10-1017-s0022112087000727": Object.freeze({
    section: "materials-and-surfaces",
    note: Object.freeze({
      en: "The dynamic-tortuosity model behind the JCA effective density.",
      es: "El modelo de tortuosidad dinámica que hay detrás de la densidad efectiva JCA.",
    }),
  }),
  "doi-10-1007-b137728": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "ISBN 978-3-540-22696-3. The standard monograph on structural vibration and its radiation: mobilities, power flow, vibration isolation, radiation efficiency and transmission across junctions.",
      es: "ISBN 978-3-540-22696-3. La monografía de referencia sobre la vibración estructural y su radiación: movilidades, flujo de potencia, aislamiento de vibraciones, eficiencia de radiación y transmisión a través de uniones.",
    }),
  }),
  "doi-10-1007-978-3-662-10118-6": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "ISBN 978-3-540-06002-4. The original derivation of the wave parameters χ and ψ and the bending-wave transmission coefficients for junctions of plates.",
      es: "ISBN 978-3-540-06002-4. La derivación original de los parámetros de onda χ y ψ y de los coeficientes de transmisión de onda de flexión para uniones de placas.",
    }),
  }),
  "book-craik-1996-sound-transmission-through-buildings-using-statistical-energy-analysis": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "ISBN 978-0-566-07572-8. The SEA treatment of airborne and structure-borne transmission in buildings, with the tabulated bending-wave transmission coefficients for X, T, L and in-line junctions.",
      es: "ISBN 978-0-566-07572-8. El tratamiento SEA de la transmisión aérea y estructural en edificios, con los coeficientes de transmisión de onda de flexión tabulados para uniones en X, T, L y en línea.",
    }),
  }),
  "std-iso-7626-1-2011": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "The FRF family and its free/blocked distinctions.",
      es: "La familia de FRF y sus distinciones libre/bloqueada.",
    }),
  }),
  "std-iso-7626-2-2015": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "The attached-exciter measurement method and its acceptance criteria.",
      es: "El método de medición con excitador acoplado y sus criterios de aceptación.",
    }),
  }),
  "std-iso-7626-5-2019": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "The impact-hammer measurement: the force and exponential windows, the average over impacts, the checks on the record and the Annex A correction.",
      es: "La medida con martillo de impacto: las ventanas de fuerza y exponencial, el promedio sobre impactos, las comprobaciones sobre el registro y la corrección del anexo A.",
    }),
  }),
  "std-iso-2041-2018": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "The damping ratio, the damping coefficient over the critical one (3.2.96), against which Formula (A.3) of ISO 7626-5 is first order.",
      es: "La relación de amortiguamiento, el coeficiente de amortiguamiento sobre el crítico (3.2.96), frente a la que la fórmula (A.3) de la ISO 7626-5 es de primer orden.",
    }),
  }),
  "std-iso-10846-1-2008": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "The blocking-force idealisation behind the dynamic transfer stiffness.",
      es: "La idealización de fuerza de bloqueo que sustenta la rigidez dinámica de transferencia.",
    }),
  }),
  "std-iso-ts-7849-1-2009": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "The upper-limit sound power from surface velocity with ε = 1.",
      es: "La potencia acústica de límite superior desde la velocidad superficial con ε = 1.",
    }),
  }),
  "std-iso-ts-7849-2-2009": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "The engineering method with a measured band-wise radiation factor.",
      es: "El método de ingeniería con un factor de radiación medido por bandas.",
    }),
  }),
  "std-iso-9611-1996": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "The free-velocity characterization of resiliently mounted sources.",
      es: "La caracterización por velocidad libre de fuentes montadas resilientemente.",
    }),
  }),
  "book-griffin-1996-handbook-of-human-vibration": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "ISBN 978-0-12-303041-2. The standard monograph on whole-body and hand-transmitted vibration: the biodynamics, discomfort and health-effect evidence behind the weightings, dose measures and exposure-response guidance of the vibration guides.",
      es: "ISBN 978-0-12-303041-2. La monografía de referencia sobre vibración de cuerpo entero y transmitida a la mano: la biodinámica, la incomodidad y la evidencia de efectos sobre la salud que sustentan las ponderaciones, las medidas de dosis y la orientación exposición-respuesta de las guías de vibración.",
    }),
  }),
  "book-mansfield-2004-human-response-to-vibration": Object.freeze({
    section: "vibration-and-structure-borne-sound",
    note: Object.freeze({
      en: "ISBN 978-0-415-28239-0. A compact modern textbook on the ISO 2631-1 and ISO 5349 evaluation chains, from perception and comfort to the occupational exposure limits.",
      es: "ISBN 978-0-415-28239-0. Un manual moderno y compacto sobre las cadenas de evaluación de ISO 2631-1 e ISO 5349, de la percepción y el confort a los límites de exposición laborales.",
    }),
  }),
  "doi-10-1007-978-94-010-0660-6": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "ISBN 978-1-4020-0390-5. The wave-based theory of outdoor sound (parabolic equation, fast field program, refraction, turbulence) behind the engineering approximations of ISO 9613-2.",
      es: "ISBN 978-1-4020-0390-5. La teoría ondulatoria del sonido en exteriores (ecuación parabólica, fast field program, refracción, turbulencia) que sustenta las aproximaciones de ingeniería de la ISO 9613-2.",
    }),
  }),
  "doi-10-1201-9780429470806": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "ISBN 978-1-4987-4007-4 (hbk), 978-0-429-47080-6 (ebk). Ground impedance models, the spherical-wave reflection coefficient behind the ground dip, meteorological effects on barriers, and the chapter 4 pressure-velocity FDTD reference model. Chapters 2 and 9 (spherical-wave ground reflection; outdoor barriers) and Chapter 11 (refraction by wind and temperature gradients, ray models and shadow zones).",
      es: "ISBN 978-1-4987-4007-4 (tapa dura), 978-0-429-47080-6 (libro electrónico). Los modelos de impedancia del suelo, el coeficiente de reflexión de onda esférica que explica el mínimo del suelo, los efectos meteorológicos sobre las barreras y el modelo FDTD presión-velocidad de referencia del capítulo 4. Capítulos 2 y 9 (reflexión de onda esférica en el suelo; barreras en exteriores) y capítulo 11 (refracción por gradientes de viento y de temperatura, modelos de rayos y zonas de sombra).",
    }),
  }),
  "doi-10-1016-0003-682x-68-90020-0": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "The screen-attenuation chart against Fresnel number that barrier engineering formulas descend from.",
      es: "El ábaco de atenuación de pantallas frente al número de Fresnel del que descienden las fórmulas de ingeniería de barreras.",
    }),
  }),
  "doi-10-2788-31776": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "The common EU noise-mapping framework, contrasted with ISO 9613-2; its flow-resistivity ground classes are reused by the rotorcraft ground effect.",
      es: "El marco común de la UE para los mapas de ruido, contrastado con la ISO 9613-2; sus clases de suelo por resistividad de flujo las reutiliza el efecto de suelo de helicópteros.",
    }),
  }),
  "std-iso-9613-1-1993": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "The pure-tone atmospheric attenuation coefficient.",
      es: "El coeficiente de atenuación atmosférica de tono puro.",
    }),
  }),
  "std-iso-9613-2-1996": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "Revised in 2024; the 1996 method is the one the library implements. The implemented outdoor attenuation chain.",
      es: "Revisada en 2024; el método de 1996 es el que implementa la biblioteca. La cadena de atenuación en exteriores implementada.",
    }),
  }),
  "std-iso-1996-1-2016": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "The environmental rating framework and its Table A.1 category adjustments.",
      es: "El marco de evaluación ambiental y sus ajustes por categoría de la Tabla A.1.",
    }),
  }),
  "std-iso-1996-2-2017": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "The environmental measurement standard: its Annex J adopts the engineering method for tonal audibility, and the audibility criterion IEC 61400-11 reuses comes from the Annex C of its 2007 edition.",
      es: "La norma de medición ambiental: su anexo J adopta el método de ingeniería para la audibilidad tonal, y el criterio de audibilidad que reutiliza la IEC 61400-11 procede del anexo C de su edición de 2007.",
    }),
  }),
  "std-nt-acou-112-2002": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "The freely downloadable onset-rate prominence method.",
      es: "El método de prominencia por tasa de crecimiento, descargable gratis.",
    }),
  }),
  "std-iso-pas-1996-3-2022": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "The ISO successor built on the NT ACOU 112 prominence: the objective onset-analysis method `impulsive_sound_adjustment` implements, from the level history $L_{p\\mathrm{AF}}$ (Clause 4), the onset detection and the least-squares onset rate (Clauses 3.3-3.5) to the prominence (Clause 5, Formula 2) and the adjustment $K_\\mathrm{I}$ (Clause 6, Formula 3).",
      es: "El sucesor ISO construido sobre la prominencia de la NT ACOU 112: el método objetivo de análisis de arranques que implementa `impulsive_sound_adjustment`, desde el historial de nivel $L_{p\\mathrm{AF}}$ (apartado 4), la detección de arranques y la tasa de crecimiento por mínimos cuadrados (apartados 3.3-3.5) hasta la prominencia (apartado 5, fórmula 2) y el ajuste $K_\\mathrm{I}$ (apartado 6, fórmula 3).",
    }),
  }),
  "std-iec-61400-11-2012-amd1-2018-csv": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "The apparent sound power geometry, wind-speed binning and tonal audibility of wind turbines.",
      es: "La geometría de potencia acústica aparente, la clasificación en intervalos de velocidad de viento y la audibilidad tonal de aerogeneradores.",
    }),
  }),
  "std-iec-ts-61400-14-2005": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "Declared values and their uncertainty for a batch of turbines.",
      es: "Los valores declarados y su incertidumbre para un lote de aerogeneradores.",
    }),
  }),
  "doi-10-1016-0003-682x-71-90024-7": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "The closed-form fit to Maekawa's chart in the Fresnel number.",
      es: "El ajuste en forma cerrada al ábaco de Maekawa en función del número de Fresnel.",
    }),
  }),
  "doi-10-1121-1-385809": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "The exact wedge-diffraction solution whose flat-wedge (thin-screen) limit the barrier insertion loss uses.",
      es: "La solución exacta de difracción en cuña cuyo límite de cuña plana (pantalla delgada) usa la pérdida por inserción de la barrera.",
    }),
  }),
  "std-en-1793-5-2016": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "The in situ sound reflection index of a road noise barrier: the signal subtraction and Adrienne window it shares with ISO 13472-1, the nine-microphone grid, the single number $DL_{RI}$ and the example of Annex B.",
      es: "El índice de reflexión acústica in situ de una pantalla de carretera: la sustracción de señales y la ventana de Adrienne que comparte con la ISO 13472-1, la rejilla de nueve micrófonos, el número único $DL_{RI}$ y el ejemplo del anexo B.",
    }),
  }),
  "doi-10-1121-1-1286811": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "Section III.D: the window that ends where the first unwanted component arrives, and the first notch of its spectrum as the low frequency limit.",
      es: "Sección III.D: la ventana que termina donde llega la primera componente no deseada, y la primera muesca de su espectro como límite de baja frecuencia.",
    }),
  }),
  "doi-10-4236-oja-2013-32a004": Object.freeze({
    section: "environment-and-transport",
    note: Object.freeze({
      en: "The QUIESST revision the 2016 edition of EN 1793-5 adopted: the nine-microphone grid, the sub-sample alignment and the directivity correction.",
      es: "La revisión de QUIESST que adoptó la edición de 2016 de la EN 1793-5: la rejilla de nueve micrófonos, la alineación por debajo de la muestra y la corrección de directividad.",
    }),
  }),
  "std-icao-annex-16-vol-i-8th-ed": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "The aircraft noise-certification standard whose Appendix 2 defines the EPNL procedure.",
      es: "La norma de certificación acústica de aeronaves cuyo Apéndice 2 define el procedimiento EPNL.",
    }),
  }),
  "std-doc-9501-3rd-ed": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "The certification guidance whose worked examples (tone correction, integrated-method EPNL) serve as numeric oracles.",
      es: "La guía de certificación cuyos ejemplos resueltos (corrección tonal, EPNL por el método integrado) sirven de oráculos numéricos.",
    }),
  }),
  "std-iec-61265-1995": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "Since revised as [IEC 61265:2018](https://webstore.iec.ch/en/publication/32635); the 1995 edition is the one the library implements. The aircraft-noise measurement-system performance tolerances.",
      es: "Revisada después como [IEC 61265:2018](https://webstore.iec.ch/en/publication/32635); la edición de 1995 es la que implementa la biblioteca. Las tolerancias de comportamiento del sistema de medida de ruido de aeronaves.",
    }),
  }),
  "std-sae-arp-5534-reaffirmed-2021": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "The SAE-Method one-third-octave-band atmospheric absorption for aircraft flyover spectra.",
      es: "La absorción atmosférica en bandas de tercio de octava por el método SAE para espectros de sobrevuelo.",
    }),
  }),
  "std-iso-3891-1978": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "Withdrawn. Annex A gives the SAE ARP 866A attenuation coefficient that ECAC Doc 29 Appendix D keeps as its legacy route; Annex C is a worked tone-correction example.",
      es: "Anulada. El anexo A da el coeficiente de atenuación de SAE ARP 866A que ofrece como vía heredada el apéndice D de la ECAC Doc 29; el anexo C es un ejemplo resuelto de corrección tonal.",
    }),
  }),
  "std-sae-arp-866b-stabilized-2012": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "The predecessor SAE atmospheric-absorption practice, source of the older 50 dB-limited Approximate Method.",
      es: "La práctica SAE de absorción atmosférica predecesora, origen del antiguo método aproximado limitado a 50 dB.",
    }),
  }),
  "std-sae-air-5662": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "The soft-ground lateral-attenuation model adopted by ECAC Doc 29.",
      es: "El modelo de atenuación lateral sobre suelo blando que adopta la ECAC Doc 29.",
    }),
  }),
  "report-european-civil-aviation-conference-2016-report-on-standard-method-of-computing-noise-contours-around-civil-airports-volume-2-technical-guide": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "The European airport noise-contour method: NPD interpolation and the single-event segment calculation. Listed with the other ECAC documents on the [ECAC documents page](https://www.ecac-ceac.org/documents/ecac-documents-and-international-agreements).",
      es: "El método europeo de contornos de ruido de aeropuerto: interpolación NPD y cálculo de evento único por segmentos. Figura con los demás documentos de ECAC en la [página de documentos de ECAC](https://www.ecac-ceac.org/documents/ecac-documents-and-international-agreements).",
    }),
  }),
  "report-european-civil-aviation-conference-2026-report-on-standard-method-of-computing-noise-contours-around-civil-airports-volume-2-technical-guide": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "Appendix D: the SAE AIR-1845 rates that normalise the NPD data and their recalculation for a non-reference atmosphere, with its worked example.",
      es: "El apéndice D: las tasas SAE AIR-1845 que normalizan los datos NPD y su recálculo para una atmósfera distinta de la de referencia, con su ejemplo resuelto.",
    }),
  }),
  "report-european-civil-aviation-conference-2026-report-on-standard-method-of-computing-noise-contours-around-civil-airports-volume-3-reference-cases-and-verification-framework": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "The reference cases and workbook used to validate the single-event chain. Listed with the other ECAC documents on the [ECAC documents page](https://www.ecac-ceac.org/documents/ecac-documents-and-international-agreements).",
      es: "Los casos de referencia y el workbook con los que se valida la cadena de evento único. Figura con los demás documentos de ECAC en la [página de documentos de ECAC](https://www.ecac-ceac.org/documents/ecac-documents-and-international-agreements).",
    }),
  }),
  "report-european-civil-aviation-conference-2026-report-on-standard-method-of-computing-rotorcraft-noise-contours": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "The standard rotorcraft contour method built on the noise hemisphere. Listed with the other ECAC documents on the [ECAC documents page](https://www.ecac-ceac.org/documents/ecac-documents-and-international-agreements).",
      es: "El método estándar de contornos de ruido de helicópteros construido sobre el hemisferio de ruido. Figura con los demás documentos de ECAC en la [página de documentos de ECAC](https://www.ecac-ceac.org/documents/ecac-documents-and-international-agreements).",
    }),
  }),
  "report-olsen-2024-rotorcraft-noise-modelling-guidance": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "The NORAH2 equation-level modelling guidance, whose tables and reference hemispheres serve as oracles. The research project is described on its [EASA project page](https://www.easa.europa.eu/en/research-projects/environmental-research-rotorcraft-noise).",
      es: "La guía de modelado NORAH2 a nivel de ecuación, cuyas tablas y hemisferios de referencia sirven de oráculos. El proyecto de investigación se describe en su [página del proyecto en EASA](https://www.easa.europa.eu/en/research-projects/environmental-research-rotorcraft-noise).",
    }),
  }),
  "doi-10-1016-0022-460x-75-90200-x": Object.freeze({
    section: "aircraft-noise",
    note: Object.freeze({
      en: "The two-ray interference solution over an impedance plane behind the rotorcraft ground effect.",
      es: "La solución de interferencia de dos rayos sobre un plano de impedancia que sustenta el efecto de suelo de helicópteros.",
    }),
  }),
  "book-urick-1983-principles-of-underwater-sound": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "Reprinted in 1996 by Peninsula Publishing. ISBN 978-0-932146-62-5. The classic monograph on underwater sound: level conventions, ship radiated noise and the sonar-equation framework.",
      es: "Reimpreso en 1996 por Peninsula Publishing. ISBN 978-0-932146-62-5. La monografía clásica del sonido submarino: convenciones de nivel, ruido radiado por buques y el marco de la ecuación del sonar.",
    }),
  }),
  "doi-10-1007-978-3-540-87662-5": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The systematic treatment of underwater acoustical quantities in the line that ISO 18405 standardised, the Weston energy-flux propagation regimes of shallow water, the sonar equations with seven fully numeric worked examples, and the orca audiogram.",
      es: "El tratamiento sistemático de las magnitudes acústicas submarinas en la línea que la ISO 18405 normalizó, los regímenes de propagación de flujo de energía de Weston en aguas someras, las ecuaciones del sonar con siete ejemplos resueltos totalmente numéricos y el audiograma de orca.",
    }),
  }),
  "book-medwin-1998-fundamentals-of-acoustical-oceanography": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "ISBN 978-0-12-487570-8. Ocean acoustics from first principles; the fluid-fluid Rayleigh reflection coefficient of the seabed model, and the closed-form travel time along the circular-arc ray of a linear sound-speed gradient (Equation 3.3.20).",
      es: "ISBN 978-0-12-487570-8. La acústica oceánica desde primeros principios; el coeficiente de reflexión de Rayleigh fluido-fluido del modelo de fondo marino, y el tiempo de propagación en forma cerrada a lo largo del rayo en arco de círculo de un gradiente lineal de velocidad del sonido (Ecuación 3.3.20).",
    }),
  }),
  "doi-10-1007-978-1-4419-8678-8": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The reference monograph on numerical propagation: normal modes, ray tracing, Gaussian beams and the parabolic equation.",
      es: "La monografía de referencia de la propagación numérica: modos normales, trazado de rayos, haces gaussianos y ecuación parabólica.",
    }),
  }),
  "doi-10-1121-1-1914492": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The canonical deep-water sound-speed profile used by the solver examples.",
      es: "El perfil canónico de velocidad del sonido en aguas profundas que usan los ejemplos de esos métodos.",
    }),
  }),
  "doi-10-1121-1-388170": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The pure-water and magnesium-sulfate halves of the reference seawater absorption model.",
      es: "Las componentes de agua pura y sulfato de magnesio del modelo de referencia de absorción en agua de mar.",
    }),
  }),
  "doi-10-1121-1-388673": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The boric-acid term and the complete total-absorption equation.",
      es: "El término de ácido bórico y la ecuación completa de absorción total.",
    }),
  }),
  "doi-10-1121-1-421258": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The legible simplified seawater absorption formula.",
      es: "La fórmula simplificada y legible de absorción en agua de mar.",
    }),
  }),
  "doi-10-1121-1-1910566": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The frequency-only low-frequency absorption formula.",
      es: "La fórmula de absorción de baja frecuencia dependiente solo de la frecuencia.",
    }),
  }),
  "doi-10-1121-1-381646": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The UNESCO international-standard sound-speed equation.",
      es: "La ecuación de velocidad del sonido UNESCO, el estándar internacional.",
    }),
  }),
  "doi-10-1121-1-413048": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The ITS-90 recast of the UNESCO sound-speed coefficients, the implemented form.",
      es: "La reformulación ITS-90 de los coeficientes UNESCO, la forma implementada.",
    }),
  }),
  "doi-10-1121-1-1903388": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The alternative pressure-based sound-speed equation.",
      es: "La ecuación alternativa de velocidad del sonido basada en presión.",
    }),
  }),
  "doi-10-1121-1-386920": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The depth-based nine-term sound-speed equation.",
      es: "La ecuación de nueve términos basada en profundidad.",
    }),
  }),
  "doi-10-1121-1-421275": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The depth-to-pressure conversion used by the sound-speed equations.",
      es: "La conversión de profundidad a presión que usan las ecuaciones de velocidad del sonido.",
    }),
  }),
  "doi-10-1121-1-1909155": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The classic ambient-noise survey behind the wind and thermal spectrum components.",
      es: "El estudio clásico del ruido ambiental que sustenta las componentes espectrales de viento y térmica.",
    }),
  }),
  "doi-10-1007-978-1-4419-7832-5": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The modern treatment of ocean ambient noise: the wind \"rule of fives\" and the Mellen thermal-noise derivation.",
      es: "El tratamiento moderno del ruido ambiental oceánico: la «regla de los cincos» del viento y la derivación del ruido térmico de Mellen.",
    }),
  }),
  "doi-10-3390-jmse9040369": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The open-access JOMOPANS-ECHO ship source-level model and its reference calculator.",
      es: "El modelo JOMOPANS-ECHO de nivel de fuente de buques (acceso abierto) y su calculadora de referencia.",
    }),
  }),
  "doi-10-1121-1-1427355": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The ensemble merchant-ship source-spectrum model.",
      es: "El modelo de espectro de conjunto de fuentes de buques mercantes.",
    }),
  }),
  "report-national-marine-fisheries-service-2018-2018-revision-to-technical-guidance-for-assessing-the-effects-of-anthropogenic-sound-on-marine-mammal-hearing-version-2-0": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The auditory weighting parameters and PTS onset thresholds of the 2018 guidance, with the Appendix D worked example.",
      es: "Los parámetros de ponderación auditiva y los umbrales de inicio de PTS de la guía de 2018, con el ejemplo resuelto del Apéndice D.",
    }),
  }),
  "report-national-marine-fisheries-service-2024-2024-update-to-technical-guidance-for-assessing-the-effects-of-anthropogenic-sound-on-marine-mammal-hearing-version-3-0": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The current U.S. guidance: revised weighting parameters and the auditory injury onset criteria that supersede the 2018 PTS thresholds.",
      es: "La guía estadounidense vigente: parámetros de ponderación revisados y los criterios de inicio de lesión auditiva que sustituyen a los umbrales de PTS de 2018.",
    }),
  }),
  "doi-10-1578-am-45-2-2019-125": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The peer-reviewed hearing groups, group audiograms and TTS/PTS onset criteria, with the errata of 45(5), 569-572.",
      es: "Los grupos auditivos, los audiogramas de grupo y los criterios de inicio de TTS y PTS revisados por pares, con la fe de erratas de 45(5), 569-572.",
    }),
  }),
  "report-finneran-2016-auditory-weighting-functions-and-tts-pts-exposure-functions-for-marine-mammals-exposed-to-underwater-noise": Object.freeze({
    section: "underwater-acoustics",
    note: Object.freeze({
      en: "The band-pass weighting-function form and the audiogram equation that the NMFS and Southall criteria both adopt.",
      es: "La forma del filtro paso banda de ponderación y la ecuación del audiograma que adoptan tanto los criterios NMFS como los de Southall.",
    }),
  }),
  "std-recommendation-itu-r-bs-1770-5": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The K-weighting pre-filter (Annex 1, Tables 1-2), the channel-weighted loudness and its two-stage gating (Annex 1, Formulae 1-7 and Table 3), the true-peak estimation guidelines (Annex 2) and the position-dependent channel weights for advanced sound systems (Annex 3, Tables 4-5), in the edition approved in November 2023. It is also the loudness algorithm behind `bext=\"loudness\"`, implemented in the broadcast area and reused when an audio file is written.",
      es: "El prefiltro de ponderación K (Anexo 1, Tablas 1-2), la sonoridad ponderada por canal y sus puertas en dos etapas (Anexo 1, Fórmulas 1-7 y Tabla 3), las directrices de estimación del pico verdadero (Anexo 2) y las ponderaciones de canal dependientes de la posición para sistemas de sonido avanzados (Anexo 3, Tablas 4-5), en la edición aprobada en noviembre de 2023. Es también el algoritmo de sonoridad tras `bext=\"loudness\"`, implementado en el área de radiodifusión y reutilizado al escribir un archivo de audio.",
    }),
  }),
  "report-american-society-of-heating-2019-ashrae-handbook-hvac-applications-si-edition-chapter-49-noise-and-vibration-control": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "ISBN 978-1-947192-13-3. The design chapter this library reads its duct walls from: Tables 29 to 34, the breakout and break-in transmission loss of a rectangular, round and flat oval duct wall band by band, and Table 40, nine machine equipment room walls, floors and ceilings with their Sound Transmission Class.",
      es: "ISBN 978-1-947192-13-3. El capítulo de diseño del que esta biblioteca lee sus paredes de conducto: las tablas 29 a 34, la pérdida por transmisión hacia fuera y hacia dentro de una pared de conducto rectangular, circular y oval plana banda a banda, y la tabla 40, nueve paredes, suelos y techos de sala de máquinas con su clase de transmisión sonora.",
    }),
  }),
  "doi-10-4324-9780203475386": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "ISBN 978-0-419-19810-9. The monograph on sound energy flux: active and reactive intensity, the p-p estimator and its phase-mismatch error budget.",
      es: "ISBN 978-0-419-19810-9. La monografía sobre el flujo de energía sonora: intensidad activa y reactiva, el estimador p-p y su balance de error por desfase.",
    }),
  }),
  "std-iso-3740-2019": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The selection guide for the sound-power family: grades, environments, source-size and background criteria.",
      es: "La guía de selección de la familia de potencia acústica: grados, entornos y criterios de tamaño de fuente y de ruido de fondo.",
    }),
  }),
  "std-iso-3741-2010": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The precision reverberation-room method.",
      es: "El método de precisión en cámara reverberante.",
    }),
  }),
  "std-iso-3743-1-2010": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The comparison with a reference sound source in a hard-walled room.",
      es: "La comparación con una fuente sonora de referencia en una sala de paredes rígidas.",
    }),
  }),
  "std-iso-3743-2-2018": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The direct and comparison methods of a special reverberation room.",
      es: "Los métodos directo y de comparación de una sala reverberante especial.",
    }),
  }),
  "std-iso-3747-2010": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The in situ comparison against a reference sound source.",
      es: "La comparación in situ con una fuente sonora de referencia.",
    }),
  }),
  "std-iso-8297-1994": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The contour round a whole industrial plant, its area, proximity and air absorption terms and the uncertainty of Table 1.",
      es: "El contorno alrededor de una planta industrial entera, sus términos de área, de proximidad y de absorción atmosférica y la incertidumbre de la Tabla 1.",
    }),
  }),
  "std-iso-3744-2010": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The enveloping-surface engineering method.",
      es: "El método de ingeniería por superficie envolvente.",
    }),
  }),
  "std-iso-3745-2012": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The precision anechoic-room method.",
      es: "El método de precisión en cámara anecoica.",
    }),
  }),
  "std-iso-4871-1996": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The noise-emission declaration: the dual/single-number forms, $L_{WAd} = L_{WA} + K_{WA}$ and the clause 6.2 verification.",
      es: "La declaración de emisión sonora: las formas de doble/único número, $L_{WAd} = L_{WA} + K_{WA}$ y la verificación del apartado 6.2.",
    }),
  }),
  "std-iso-9614-1-1993": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The field indicators and the dynamic-capability criterion of intensity measurement.",
      es: "Los indicadores de campo y el criterio de capacidad dinámica de la medida de intensidad.",
    }),
  }),
  "std-iec-61043-1993": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "Adopted in Europe as EN 61043:1994. The p-p instrument standard: the cross-spectral estimator and the residual pressure-intensity index.",
      es: "Adoptada en Europa como EN 61043:1994. La norma de instrumentación p-p: el estimador por espectro cruzado y el índice presión-intensidad residual.",
    }),
  }),
  "doi-10-1002-9781118443767": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The transfer-matrix formulation, the element matrices and the transmission loss from the compound matrix (Eq. (3.27)), and the reference treatment of dissipative and combined mufflers.",
      es: "La formulación por matrices de transferencia, las matrices de cada elemento y la pérdida por transmisión a partir de la matriz compuesta (Ec. (3.27)), y el tratamiento de referencia de los silenciadores disipativos y combinados.",
    }),
  }),
  "report-farina-2000-simultaneous-measurement-of-impulse-response-and-distortion-with-a-swept-sine-technique": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The exponential-sweep deconvolution and the L·ln(n) packing of the harmonic impulse responses ahead of the linear one.",
      es: "La deconvolución del barrido exponencial y el empaquetado L·ln(n) de las respuestas al impulso armónicas por delante de la lineal.",
    }),
  }),
  "article-muller-2001-transfer-function-measurement-with-sweeps": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The sweep-measurement monograph behind the practice notes: inverse filters, fades and distortion rejection, and the synthesis of a sweep from a magnitude spectrum and a group delay (Secs. 4.2-4.3).",
      es: "La monografía de medición con barridos detrás de las notas de práctica: filtros inversos, fundidos y rechazo de la distorsión, y la síntesis de un barrido a partir de un espectro de magnitud y un retardo de grupo (Secs. 4.2-4.3).",
    }),
  }),
  "doi-10-17743-jaes-2015-0071": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The synchronization condition that makes harmonic phases system properties, the closed-form inverse-filter spectrum used for the deconvolution and the fractional-sample separation.",
      es: "La condición de sincronización que convierte las fases de los armónicos en propiedades del sistema, el espectro del filtro inverso en forma cerrada que se usa para la deconvolución y la separación con resolución de muestra fraccionaria.",
    }),
  }),
  "std-ebu-r-128": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The −23.0 LUFS target level, the −1 dBTP ceiling and the normalisation practice built on them.",
      es: "El nivel objetivo de −23,0 LUFS, el techo de −1 dBTP y la práctica de normalización construida sobre ellos.",
    }),
  }),
  "std-ebu-tech-3341": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The momentary, short-term and integrated time scales, and the Table 1 minimum-requirements test signals with their tolerances, which are synthesizable and are what the implementation is checked against.",
      es: "Las escalas temporales momentánea, de corto plazo e integrada, y las señales de prueba de requisitos mínimos de su Tabla 1 con sus tolerancias, que son sintetizables y son con las que se comprueba la implementación.",
    }),
  }),
  "std-ebu-tech-3342": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The loudness range algorithm, its reference implementation and its Table 1 test signals, matched to ±1 LU.",
      es: "El algoritmo del rango de sonoridad, su implementación de referencia y las señales de prueba de su Tabla 1, reproducidas dentro de ±1 LU.",
    }),
  }),
  "std-ebu-tech-3343": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "The production practice behind the numbers: what to normalise, when, and what a loudness target does and does not constrain.",
      es: "La práctica de producción que hay detrás de los números: qué normalizar, cuándo, y qué restringe y qué no restringe un objetivo de sonoridad.",
    }),
  }),
  "article-steinmetz-2021-pyloudnorm-a-simple-yet-flexible-loudness-meter-in-python": Object.freeze({
    section: "sources-and-devices",
    note: Object.freeze({
      en: "An independent BS.1770 implementation, useful as a cross-check on a gated-loudness result.",
      es: "Una implementación independiente de BS.1770, útil como contraste de un resultado de sonoridad con puertas.",
    }),
  }),
  "doi-10-1016-b978-0-12-753960-7-x5000-1": Object.freeze({
    section: "wave-simulation",
    note: Object.freeze({
      en: "The Helmholtz integral equation behind the near-to-far-field transformation, with the outgoing free-space Green function and the far-field limit.",
      es: "La ecuación integral de Helmholtz tras la transformación de campo cercano a campo lejano, con la función de Green de espacio libre saliente y el límite de campo lejano.",
    }),
  }),
  "doi-10-1190-1-1442147": Object.freeze({
    section: "wave-simulation",
    note: Object.freeze({
      en: "The elastic velocity-stress scheme on the fully staggered cell, its Courant bound and dispersion relations, and the liquid as the shear-free limit.",
      es: "El esquema elástico velocidad-esfuerzo sobre la celda totalmente escalonada, su cota de Courant y sus relaciones de dispersión, y el líquido como límite sin cizalla.",
    }),
  }),
  "doi-10-2478-v10155-010-0084-x": Object.freeze({
    section: "wave-simulation",
    note: Object.freeze({
      en: "The heterogeneous effective grid parameters (harmonic shear modulus, arithmetic density) and the stress-imaging free surface.",
      es: "Los parámetros efectivos de malla en medio heterogéneo (módulo de cizalla armónico, densidad aritmética) y la superficie libre por imagen de esfuerzos.",
    }),
  }),
  "doi-10-1007-978-3-642-52369-4": Object.freeze({
    section: "wave-simulation",
    note: Object.freeze({
      en: "The fluid-solid oracles: the oblique reflection coefficient with mode conversion, the exact Scholte characteristic equation and the three-media layer transmission.",
      es: "Los oráculos fluido-sólido: el coeficiente de reflexión oblicua con conversión de modo, la ecuación característica exacta de Scholte y la transmisión de la capa de tres medios.",
    }),
  }),
  "doi-10-1190-1-1468623": Object.freeze({
    section: "wave-simulation",
    note: Object.freeze({
      en: "The fluid-solid benchmark of the staggered scheme: the effective-parameter averages, the Scholte configuration of water over a 3500/2000/2500 seabed and the points-per-wavelength rule for interface waves.",
      es: "El benchmark fluido-sólido del esquema escalonado: las medias de los parámetros efectivos, la configuración de Scholte del agua sobre un lecho 3500/2000/2500 y la regla de puntos por longitud de onda para las ondas de interfase.",
    }),
  }),
  "std-jcgm-100-2008-the-gum": Object.freeze({
    section: "metrology",
    note: Object.freeze({
      en: "The law of propagation of uncertainty implemented by the uncertainty module.",
      es: "La ley de propagación de la incertidumbre implementada por el módulo de incertidumbre.",
    }),
  }),
  "std-jcgm-101-2008": Object.freeze({
    section: "metrology",
    note: Object.freeze({
      en: "The Monte Carlo propagation of distributions implemented by the Monte Carlo uncertainty engine.",
      es: "La propagación de distribuciones mediante Monte Carlo implementada por el motor de incertidumbre de Monte Carlo.",
    }),
  }),
  "std-iso-12999-1-2020": Object.freeze({
    section: "metrology",
    note: Object.freeze({
      en: "The domain-specific reproducibility budget for building-acoustics single-number ratings, the companion to the general GUM machinery.",
      es: "El balance de reproducibilidad específico de la acústica de la edificación para magnitudes de número único, complemento de la maquinaria general de la GUM.",
    }),
  }),
  "doi-10-1214-aoms-1177731909": Object.freeze({
    section: "metrology",
    note: Object.freeze({
      en: "The exact conditional distribution of the number of runs, from which the runs-about-the-median acceptance regions are computed.",
      es: "La distribución condicional exacta del número de rachas, de la que se calculan las regiones de aceptación de las rachas en torno a la mediana.",
    }),
  }),
  "doi-10-1002-j-1538-7305-1945-tb00453-x": Object.freeze({
    section: "metrology",
    note: Object.freeze({
      en: "The original derivations of the expected level-crossing and maxima rates and the peak distribution of Gaussian noise that Bendat & Piersol Section 5.5 presents (their Ref. 6; Parts I-II are in volume 23, 1944).",
      es: "Las deducciones originales de las tasas esperadas de cruces por nivel y de máximos y de la distribución de picos del ruido gaussiano que presentan Bendat y Piersol en su apartado 5.5 (su Ref. 6; las partes I-II están en el volumen 23, de 1944).",
    }),
  }),
});
