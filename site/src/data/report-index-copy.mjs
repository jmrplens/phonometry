/**
 * The words the report index prints around its rows, in both languages.
 *
 * They lived inside `ReportIndex.astro` until the Markdown copy of the page
 * needed them too: `ReportIndex.md.mjs` writes the same index for a reader
 * of the copy, and two hand-kept sets of area names would drift the first
 * time one of them was edited. Both import them from here.
 */

/** What each documentation area is called, in each language. */
export const AREAS = {
  aircraft: { en: 'Aircraft noise', es: 'Ruido de aeronaves' },
  buildings: { en: 'Buildings and rooms', es: 'Edificios y salas' },
  devices: { en: 'Devices and noise control', es: 'Dispositivos y control de ruido' },
  environment: { en: 'Environment and transport', es: 'Medio ambiente y transporte' },
  materials: { en: 'Materials and surfaces', es: 'Materiales y superficies' },
  perception: { en: 'Hearing and perception', es: 'Audición y percepción' },
  signals: { en: 'Signal analysis', es: 'Análisis de señal' },
  vibration: { en: 'Vibration', es: 'Vibración' },
  underwater: { en: 'Underwater acoustics', es: 'Acústica submarina' },
  simulation: { en: 'Simulation', es: 'Simulación' },
  fluids: { en: 'The medium', es: 'El medio' },
  solids: { en: 'Elastic solids', es: 'Sólidos elásticos' },
};

/*
 * One area holds a single fiche (aircraft noise, today), and a count written
 * without a singular reads "1 fiches" there in English and "1 fichas" in
 * Spanish. Both are published prose, so both get the singular.
 */
export const COPY = {
  en: { source: 'Shown in', count: (n) => `${n} ${n === 1 ? 'fiche' : 'fiches'}` },
  es: { source: 'Se muestra en', count: (n) => `${n} ${n === 1 ? 'ficha' : 'fichas'}` },
};

/**
 * An area's name in a language, or its key when the table has no row for it.
 *
 * @param {string} key
 * @param {'en' | 'es'} lang
 * @returns {string}
 */
export const areaName = (key, lang) => AREAS[key]?.[lang] ?? key;

/**
 * The fiche groups in the order the index lists them: by area name, as each
 * language sorts it.
 *
 * @template T
 * @param {Record<string, T[]>} groups
 * @param {'en' | 'es'} lang
 * @returns {[string, T[]][]}
 */
export const sortedAreas = (groups, lang) =>
  Object.entries(groups).sort(([a], [b]) => areaName(a, lang).localeCompare(areaName(b, lang), lang));
