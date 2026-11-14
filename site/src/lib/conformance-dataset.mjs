/**
 * The conformance report as a schema.org Dataset, in the page's language.
 *
 * The report page carried its Dataset as a block of its own in the
 * frontmatter: an English name, technique and column descriptions on the
 * Spanish page too, no version and no date, the concept DOI of the software
 * as its identifier, and the script that writes it as the one thing it was
 * based on. It is now the `mainEntity` of the page's article, in the graph
 * src/components/Head.astro writes, and says:
 *
 * - which version of the library it was generated for (`version`, the
 *   artefact's own `library`), and the day its data last changed
 *   (`dateModified`, the last commit of `docs/conformance.json`; the page is
 *   dated by its component and its text as well, and a change to how the
 *   rows are drawn changes no value in them);
 * - what it is based on: the script that writes it, and every standard its
 *   checks quote, each named as the bibliography defines it, so the MIT
 *   licence it carries is read as covering the report and not the values the
 *   standards publish;
 * - its name, technique and columns in the page's language;
 * - where its files are downloaded from, and where the script is read: each
 *   at the commit its rows are of, the one the page's banner names, never at
 *   a branch. The artefact carries no date and no commit of its own, so a
 *   copy of this record that pointed at main would hand out whatever main
 *   holds by then, with nothing in the file to say it is not the one
 *   described.
 *
 * The software's DOI is not the Dataset's: it names every version of the
 * library, and a report is the record of one.
 */

/** What the Dataset says in each language; the counts are filled in from the report. */
const TEXT = {
  en: {
    name: 'phonometry numerical conformance report',
    description: ({ checks, domains, designations, sources }) =>
      `${checks} numerical conformance checks pinning each implemented acoustic metric to a clause, table or ` +
      'worked example of the governing standard, with the normative expected value, the value phonometry ' +
      `computes, the delta and a pass/fail verdict, across ${domains} domains, against ${designations} ` +
      `normative designations and ${sources} further published sources. Regenerated and enforced by CI on ` +
      'every pull request.',
    measurementTechnique:
      'Comparison of computed values against the normative expected values published in the governing ' +
      'standards (tolerance tables and worked examples).',
    variables: [
      ['Standard', 'Governing standard and clause or table'],
      ['Quantity', 'Acoustic quantity under test'],
      ['Expected', 'Normative value published in the standard'],
      ['Computed', 'Value computed by phonometry'],
      ['Delta', 'Signed difference between computed and expected'],
      ['Limit', 'Published tolerance the deviation is judged against'],
      ['Used', 'Fraction of the published tolerance the deviation consumes'],
      ['Status', "Verdict against the standard's tolerance: pass, fail, by design or not applicable"],
    ],
  },
  es: {
    name: 'Informe numérico de conformidad de phonometry',
    description: ({ checks, domains, designations, sources }) =>
      `${checks} comprobaciones numéricas de conformidad que anclan cada métrica acústica implementada a un ` +
      'apartado, tabla o ejemplo resuelto de la norma que la rige, con el valor normativo esperado, el valor ' +
      `que calcula phonometry, la diferencia y un veredicto, sobre ${domains} dominios, frente a ` +
      `${designations} designaciones normativas y ${sources} fuentes publicadas adicionales. Se regenera y se ` +
      'verifica en CI en cada pull request.',
    measurementTechnique:
      'Comparación de los valores calculados con los valores esperados normativos que publican las normas que ' +
      'los rigen (tablas de tolerancias y ejemplos resueltos).',
    variables: [
      ['Norma', 'Norma que rige y su apartado o tabla'],
      ['Magnitud', 'Magnitud acústica que se comprueba'],
      ['Esperado', 'Valor normativo que publica la norma'],
      ['Calculado', 'Valor que calcula phonometry'],
      ['Desviación', 'Diferencia con signo entre el valor calculado y el esperado'],
      ['Límite', 'Tolerancia publicada frente a la que se juzga la desviación'],
      ['Consumido', 'Fracción de la tolerancia publicada que consume la desviación'],
      ['Estado', 'Veredicto frente a la tolerancia de la norma: cumple, no cumple, por diseño o no aplica'],
    ],
  },
};

/** The script that writes the report, which the Dataset is also based on. */
const GENERATOR = 'scripts/conformance_report.py';

/** The committed artefact and its Markdown rendering, which the Dataset hands out. */
const DOWNLOADS = [
  ['application/json', 'docs/conformance.json'],
  ['text/markdown', 'docs/CONFORMANCE.md'],
];

/**
 * The Dataset node of the report page.
 *
 * @param {object} options
 * @param {'en' | 'es'} options.lang
 * @param {string} options.canonical The page's absolute URL.
 * @param {{ library: string, counts: { checks: number, domains: number, designations: number, sources: number } }} options.report
 * @param {string} options.modified The day the data last changed, YYYY-MM-DD.
 * @param {string} options.commit The commit that last changed the data, 40
 *   hexadecimal digits: every file of the repository the node names is read
 *   at it.
 * @param {object[]} options.standards The works the checks quote, as the
 *   short nodes a page names them with (src/lib/citations.mjs, `referenceStub`).
 * @param {string} options.personId
 * @param {string} options.softwareId
 */
export function conformanceDataset({ lang, canonical, report, modified, commit, standards, personId, softwareId }) {
  if (!/^[0-9a-f]{40}$/.test(String(commit))) {
    throw new Error(`the conformance report's Dataset needs the commit its rows are of, 40 hexadecimal digits, not ${JSON.stringify(commit)}`);
  }
  const text = TEXT[lang];
  return {
    '@type': 'Dataset',
    '@id': `${canonical}#dataset`,
    name: text.name,
    description: text.description(report.counts),
    url: canonical,
    inLanguage: lang,
    version: report.library,
    dateModified: modified,
    license: 'https://opensource.org/license/MIT',
    isAccessibleForFree: true,
    creator: { '@id': personId },
    publisher: { '@id': personId },
    about: { '@id': softwareId },
    measurementTechnique: text.measurementTechnique,
    variableMeasured: text.variables.map(([name, description]) => ({ '@type': 'PropertyValue', name, description })),
    distribution: DOWNLOADS.map(([encodingFormat, path]) => ({
      '@type': 'DataDownload',
      encodingFormat,
      contentUrl: `https://raw.githubusercontent.com/jmrplens/phonometry/${commit}/${path}`,
    })),
    isBasedOn: [`https://github.com/jmrplens/phonometry/blob/${commit}/${GENERATOR}`, ...standards],
  };
}
