/**
 * The words a catalogue's table prints around its rows, in both languages,
 * and the rules that pick them for one catalogue.
 *
 * They lived inside `Catalogues.astro` until the Markdown copy of each
 * catalogue page needed them too: `Catalogues.md.mjs` writes the same table
 * for a reader of the copy, under the same row heading and column headings,
 * with the same words for each kind of cell, and two hand-kept sets of them
 * would drift the first time one of them was edited. Both import them from
 * here.
 *
 * @module
 */

/** @typedef {import('../generated/catalogues.mjs').CatalogueCell} CatalogueCell */
/** @typedef {import('../generated/catalogues.mjs').CatalogueRow} CatalogueRow */
/** @typedef {import('../generated/catalogues.mjs').CatalogueTextField} CatalogueTextField */
/** @typedef {'en' | 'es'} Lang */

// The search placeholders are suggestions a reader types, so each one has to
// find rows on the page it is shown on. The Spanish page matches the Spanish
// words the generator attached to every row as well as the book's own English,
// so its suggestions are Spanish; they were English, on purpose, while the
// Spanish page matched only the book's words and "hierba" found nothing.
// scripts/check-reference-pages.mjs types every word of every suggestion into
// the finder of each catalogue page, in each language, and checks that it
// still finds a row of its own catalogue.
export const COPY = {
  en: {
    search: 'Filter by material',
    searchGas: 'Filter by gas',
    searchFacing: 'Filter by facing',
    searchFloor: 'Filter by floor',
    searchDuct: 'Filter by duct',
    searchCondition: 'Filter by condition',
    searchPlaceholder: 'steel, foam, glass',
    groundPlaceholder: 'grass, snow, asphalt',
    gasPlaceholder: 'methane, argon, steam',
    liquidPlaceholder: 'water, ethanol, mercury',
    treatmentPlaceholder: 'muescado, alfombra',
    carpetPlaceholder: 'nylon, lana, rizo',
    resilientModulusPlaceholder: 'rock wool, cork',
    solidNonlinearityPlaceholder: 'FCC, NaCl, ionic',
    absorptionPlaceholder: 'carpet, plaster, velour',
    partitionPlaceholder: 'brick, door, glass',
    scatteringPlaceholder: 'pyramid, hemisphere, holly',
    woodPlaceholder: 'spruce, maple',
    plateauPlaceholder: 'steel, glass, brick',
    porousPlaceholder: 'glass wool, foam, felt',
    areaPlaceholder: 'audience, musician, air',
    geometryPlaceholder: 'h/L = 20, w = 10 cm',
    fluidPlaceholder: 'water, mercury, steam',
    diffusionPlaceholder: 'semiellipse, triangle, QRD',
    dampingPlaceholder: 'DYAD, ISD, Soundcoat',
    facingPlaceholder: 'FM 125, 1584, 40',
    resilientPlaceholder: 'polystyrene, wool, foam',
    floorPlaceholder: 'hormigón, moqueta, viguetas',
    ductPlaceholder: '610, round, break-in',
    conditionPlaceholder: '20 °C, 50-70',
    empty: 'No row matches that filter.',
    material: 'Material',
    surface: 'Surface',
    gas: 'Gas',
    finish: 'Finish',
    partition: 'Construction',
    facing: 'Facing',
    floor: 'Floor or treatment',
    duct: 'Duct',
    condition: 'Condition',
    state: 'State',
    substance: 'Substance',
    treatment: 'Treatment',
    construction: 'Construction',
    structure: 'Material or structure',
    conditions: 'Conditions',
    mounting: 'Mount',
    per: 'Per',
    solver: 'Computed with',
    direction: 'Direction',
    shape: 'Shape',
    gauge: 'Sheet gauge',
    weave: 'Weave',
    bonding: 'Bonding',
    fixedBy: 'What fixes it',
    source: 'Source',
    regionLabel: 'Published values, scrollable sideways',
    legend: 'Italic is a value this library worked out; a dotted underline is a cell that is not a plain number, and what it is reads on the cell; an asterisk is a note the page made about the row. Click a mark to read it, or give the table focus and press Enter to walk the marks with the arrow keys.',
    kinds: {
      printed: 'as the page prints it',
      fixed: 'what the model or the standard beside it fixes',
      derived: 'worked out by this library',
      converted: 'converted from the page\'s figure',
      carried: 'the page gives this value on another of its rows',
      approximate: 'the page prints it with a tilde',
      estimated: 'the page marks it as an estimate, not a measurement',
      range: 'the page prints an interval',
      bound: 'the page prints a bound and no value',
      reported: 'the page lists several readings',
      unquantified: 'the page prints a word here',
    },
  },
  es: {
    search: 'Filtrar por material',
    searchGas: 'Filtrar por gas',
    searchFacing: 'Filtrar por velo',
    searchFloor: 'Filtrar por suelo',
    searchDuct: 'Filtrar por conducto',
    searchCondition: 'Filtrar por condición',
    searchPlaceholder: 'acero, espuma, vidrio',
    groundPlaceholder: 'hierba, nieve, asfalto',
    gasPlaceholder: 'metano, argón, vapor',
    liquidPlaceholder: 'agua, etanol, mercurio',
    treatmentPlaceholder: 'muescado, alfombra',
    carpetPlaceholder: 'nylon, lana, rizo',
    resilientModulusPlaceholder: 'lana de roca, corcho',
    solidNonlinearityPlaceholder: 'FCC, NaCl, iónico',
    absorptionPlaceholder: 'moqueta, yeso, terciopelo',
    partitionPlaceholder: 'ladrillo, puerta, vidrio',
    scatteringPlaceholder: 'pirámide, semiesfera, acebo',
    woodPlaceholder: 'pícea, arce',
    plateauPlaceholder: 'acero, vidrio, ladrillo',
    porousPlaceholder: 'lana de vidrio, espuma, fieltro',
    areaPlaceholder: 'público, músico, aire',
    geometryPlaceholder: 'h/L = 20, w = 10 cm',
    fluidPlaceholder: 'agua, mercurio, vapor',
    diffusionPlaceholder: 'semielipse, triángulo, QRD',
    dampingPlaceholder: 'DYAD, ISD, Soundcoat',
    facingPlaceholder: 'FM 125, 1584, 40',
    resilientPlaceholder: 'poliestireno, lana, espuma',
    floorPlaceholder: 'hormigón, moqueta, viguetas',
    ductPlaceholder: '610, circular, entrada',
    conditionPlaceholder: '20 °C, 50-70',
    empty: 'Ninguna fila coincide con ese filtro.',
    material: 'Material',
    surface: 'Superficie',
    gas: 'Gas',
    finish: 'Acabado',
    partition: 'Construcción',
    facing: 'Velo resistivo',
    floor: 'Suelo o tratamiento',
    duct: 'Conducto',
    condition: 'Condición',
    state: 'Estado',
    substance: 'Sustancia',
    treatment: 'Tratamiento',
    construction: 'Construcción',
    structure: 'Material o estructura',
    conditions: 'Condiciones',
    mounting: 'Montaje',
    per: 'Por',
    solver: 'Calculado con',
    direction: 'Dirección',
    shape: 'Forma',
    gauge: 'Calibre de chapa',
    weave: 'Tejido',
    bonding: 'Enlace',
    fixedBy: 'Qué lo fija',
    source: 'Fuente',
    regionLabel: 'Valores publicados, con desplazamiento lateral',
    legend: 'La cursiva es un valor calculado por esta biblioteca; el subrayado punteado es una celda que no es un número a secas, y lo que es se lee en la propia celda; el asterisco es una nota que la página hace sobre la fila. Haz clic en una marca para leerla, o pon el foco en la tabla y pulsa Intro para recorrerlas con las flechas.',
    kinds: {
      printed: 'tal como lo imprime la página',
      fixed: 'lo que fija el modelo o la norma que lleva al lado',
      derived: 'calculado por esta biblioteca',
      converted: 'convertido desde la cifra de la página',
      carried: 'la página da este valor en otra de sus filas',
      approximate: 'la página lo imprime con una tilde',
      estimated: 'la página lo marca como estimación, no como medida',
      range: 'la página imprime un intervalo',
      bound: 'la página imprime una cota, no un valor',
      reported: 'la página enumera varias lecturas',
      unquantified: 'la página imprime una palabra aquí',
    },
  },
};

/**
 * The three things a catalogue is asked for by name: what its filter is
 * called, what it suggests you type into it and what its first column holds.
 *
 * A lookup and not a chain of conditionals, because with seventeen catalogues
 * the chain was seven deep before this and the entry for a new one has to be
 * one line in an obvious place rather than a nesting level. Anything not
 * named here is a table of materials, which is what most of them are.
 *
 * @param {string} section  The catalogue's key in `catalogues.mjs`.
 * @param {Lang} lang
 */
export function catalogueWords(section, lang) {
  const copy = COPY[lang];

  /**
   * What the filter is called, which is not a material in every catalogue.
   *
   * @type {Record<string, string>}
   */
  const searchLabels = {
    gases: copy.searchGas,
    flowResistance: copy.searchFacing,
    impactInsulation: copy.searchFloor,
    ductTransmissionLoss: copy.searchDuct,
    airAttenuation: copy.searchCondition,
  };

  /**
   * What to search for, which is not a material in the ground catalogue.
   *
   * @type {Record<string, string>}
   */
  const placeholders = {
    ground: copy.groundPlaceholder,
    gases: copy.gasPlaceholder,
    absorption: copy.absorptionPlaceholder,
    absorptionAreas: copy.areaPlaceholder,
    orthotropicWood: copy.woodPlaceholder,
    plateau: copy.plateauPlaceholder,
    porous: copy.porousPlaceholder,
    predictedScattering: copy.geometryPlaceholder,
    fluids: copy.fluidPlaceholder,
    transmissionLoss: copy.partitionPlaceholder,
    scattering: copy.scatteringPlaceholder,
    diffusion: copy.diffusionPlaceholder,
    damping: copy.dampingPlaceholder,
    flowResistance: copy.facingPlaceholder,
    resilientLayers: copy.resilientPlaceholder,
    /* The impact insulation is the second catalogue after Arau's absorption
       whose rows are printed in Spanish, and this one is printed in Spanish in
       both languages of this page: the handbook it comes from is a Spanish
       translation, the row is a paragraph describing a floor, and a reader
       typing "concrete" into an English page finds nothing. */
    impactInsulation: copy.floorPlaceholder,
    ductTransmissionLoss: copy.ductPlaceholder,
    airAttenuation: copy.conditionPlaceholder,
    nonlinearity: copy.liquidPlaceholder,
    dampingTreatments: copy.treatmentPlaceholder,
    carpets: copy.carpetPlaceholder,
    resilientModuli: copy.resilientModulusPlaceholder,
    solidNonlinearity: copy.solidNonlinearityPlaceholder,
  };

  /**
   * What the first column holds, which is not a material in every catalogue.
   *
   * @type {Record<string, string>}
   */
  const rowHeadings = {
    fluids: copy.state,
    nonlinearity: copy.substance,
    solidNonlinearity: copy.structure,
    dampingTreatments: copy.treatment,
    carpets: copy.construction,
    ground: copy.surface,
    gases: copy.gas,
    absorption: copy.finish,
    absorptionAreas: copy.finish,
    transmissionLoss: copy.partition,
    scattering: copy.surface,
    diffusion: copy.surface,
    predictedScattering: copy.surface,
    flowResistance: copy.facing,
    impactInsulation: copy.floor,
    ductTransmissionLoss: copy.duct,
    airAttenuation: copy.condition,
  };

  return {
    copy,
    searchLabel: searchLabels[section] ?? copy.search,
    placeholder: placeholders[section] ?? copy.searchPlaceholder,
    rowHeading: rowHeadings[section] ?? copy.material,
  };
}

/**
 * @typedef {object} TextColumn
 * @property {'mounting' | 'per' | 'direction' | 'shape' | 'gauge' | 'weave' | 'bonding' | 'model'} field
 * @property {string} label  Its heading, in the page's language.
 * @property {boolean} wrap  Whether its value is a phrase that wraps.
 */

/*
 * The columns that hold a word rather than a quantity, each appearing when a
 * row of this catalogue fills it, which is the rule the quantity columns
 * follow: no catalogue pays a column for what another one carries. Every one
 * of them is the thing that tells two otherwise identical rows apart.
 *
 * The mount, because the same board on the floor and over a 400 mm airspace
 * is two rows of one name with different numbers. What an area is an area of,
 * because an audience is priced per person and the air per cubic metre and
 * both are printed in square metres. Which solver produced a row, because a
 * coefficient a boundary element model computed and one a reverberation room
 * measured are the same number and not the same evidence. Which way the sound
 * crossed a duct wall, what shape that duct is and what gauge its sheet was,
 * because the six duct tables print one size in six rows. And how a glass
 * cloth is woven, which is the column its own page prints where the wire mesh
 * table prints a wire count.
 *
 * `wrap` is what the value asks for rather than a style: a word or two sits
 * on its line, and only the phrase columns need the block that caps their
 * width. The order is the order they are declared in, and the solver stays
 * last because it is the widest.
 */
const TEXT_COLUMNS = /** @type {const} */ ([
  { field: 'mounting', label: 'mounting', wrap: false },
  { field: 'per', label: 'per', wrap: true },
  { field: 'direction', label: 'direction', wrap: false },
  { field: 'shape', label: 'shape', wrap: false },
  { field: 'gauge', label: 'gauge', wrap: false },
  { field: 'weave', label: 'weave', wrap: false },
  { field: 'bonding', label: 'bonding', wrap: false },
  /* The fluids carry a model too, and it is what fixes the state rather than
     a solver that computed a row, so it is the last column of that table and
     not one of these. */
  { field: 'model', label: 'solver', wrap: true, notOn: 'fluids' },
]);

/**
 * The word columns one catalogue shows: those some row of it fills.
 *
 * @param {string} section  The catalogue's key.
 * @param {readonly CatalogueRow[]} rows  Its rows.
 * @param {Lang} lang
 * @returns {TextColumn[]}
 */
export function textColumns(section, rows, lang) {
  const copy = COPY[lang];
  return TEXT_COLUMNS.filter(
    (column) => !('notOn' in column && column.notOn === section) && rows.some((row) => row[column.field]),
  ).map((column) => ({ field: column.field, label: copy[column.label], wrap: column.wrap }));
}

/**
 * A column's heading in the language its page is published in.
 *
 * @param {{ heading: string, headingEs?: string }} column
 * @param {Lang} lang
 * @returns {string}
 */
export const columnHeading = (column, lang) => (lang === 'es' && column.headingEs) || column.heading;

/**
 * A row's words on a page. The Spanish page prints the Spanish the generator
 * attached to the row, where there is one; the English page, and a row whose
 * book already prints Spanish, print what the row carries.
 *
 * @param {CatalogueRow} row
 * @param {CatalogueTextField | 'gauge'} field
 * @param {Lang} lang
 * @returns {string}
 */
export const say = (row, field, lang) =>
  (lang === 'es' && field !== 'gauge' && row.es?.[field]) || row[field] || '';

/**
 * A cell's text on a page: a range reads "0,4 a 0,8" in Spanish.
 *
 * @param {CatalogueCell} cell
 * @param {Lang} lang
 * @returns {string}
 */
export const cellText = (cell, lang) => (lang === 'es' && cell.textEs) || cell.text;

/**
 * A cell's note on a page, in its language.
 *
 * @param {CatalogueCell} cell
 * @param {Lang} lang
 * @returns {string}
 */
export const cellNote = (cell, lang) => (lang === 'es' && cell.noteEs) || cell.note;

/**
 * The title a marked cell carries: the page's own note when it made one,
 * otherwise what the mark means, and for a converted cell the figure and the
 * unit the page printed after it. A number the page simply printed has
 * nothing to explain and carries none.
 *
 * @param {CatalogueCell} cell
 * @param {Lang} lang
 * @returns {string | undefined}
 */
export function cellTitle(cell, lang) {
  const kinds = COPY[lang].kinds;
  return (
    cellNote(cell, lang) ||
    (cell.kind === 'printed' || cell.kind === 'absent'
      ? undefined
      : cell.printed
        ? `${kinds[cell.kind]}: ${cell.printed}`
        : kinds[cell.kind])
  );
}
