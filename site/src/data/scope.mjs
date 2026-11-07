/**
 * What the library covers, in the one shape the structured data needs.
 *
 * The `SoftwareApplication` node used to carry a hand-written description and
 * an eight-item `featureList`, both written when the project was a fractional
 * octave filter bank and neither updated as it grew into a toolkit spanning
 * building acoustics, psychoacoustics, underwater and aircraft noise. The
 * visible `<meta name="description">` said one thing and the machine-readable
 * node said another, and a model reading the page takes the machine-readable
 * one.
 *
 * So the feature list is derived here from `home.ts`, which already holds the
 * areas and the standards actually implemented in each and is what the
 * landing page renders. Adding an area to the landing page now adds it to the
 * structured data, with nothing to keep in step by hand.
 *
 * The site is written in English and in Spanish, and the site-wide graph is
 * one block, the same on every page, so every text in it is given in both
 * languages, each tagged with its own: a Spanish page used to describe the
 * software in English alone. Both landing pages are read, each in its own
 * language.
 */
import { en, es } from './home.ts';
import { designations, domains, sources, totalChecks } from './conformance-stats.mjs';

/** The landing page in each language the site is written in. */
const HOME = { en, es };
const LANGUAGES = /** @type {const} */ (['en', 'es']);

/**
 * A text in one language, as JSON-LD writes it.
 *
 * @param {string} value The text.
 * @param {'en'|'es'} language Its language.
 */
const tagged = (value, language) => ({ '@value': value, '@language': language });

/**
 * The two texts of `texts` as one language-tagged value, English first.
 *
 * @param {{en: string, es: string}} texts The same text in each language.
 */
export const inBothLanguages = (texts) => LANGUAGES.map((language) => tagged(texts[language], language));

/**
 * One `featureList` entry per documented area, in one language: the area,
 * what it does, and the designations implemented there, under the heading
 * the landing page gives that column. Schema.org wants short human-readable
 * strings, so this is the area summary plus its standards rather than a dump
 * of every function. An area no standard governs states none: the placeholder
 * its row shows is a label for the reader, not a standard.
 */
const featuresOf = ({ coverage }) =>
  coverage.areas.map((area) =>
    area.standards.length > 0
      ? `${area.name}: ${area.summary} ${coverage.headers[1]}: ${area.standards.join(', ')}.`
      : `${area.name}: ${area.summary}`,
  );

/** The feature list in each language, one entry per area, in the order the landing page lists them. */
export const featureLists = { en: featuresOf(en), es: featuresOf(es) };

/** The feature list as the software node publishes it: every entry, tagged with its language. */
export const featureList = LANGUAGES.flatMap((language) =>
  featureLists[language].map((feature) => tagged(feature, language)),
);

/**
 * The scope sentence, with the conformance counts interpolated so it cannot
 * fall behind the report.
 *
 * `src/content/docs/index.mdx` states the same counts in its frontmatter
 * `description`, because Starlight frontmatter is static and cannot import.
 * `scripts/check_conformance_claims.py` fails the build if the counts in that
 * copy drift from the report, which is the part that actually went wrong
 * before.
 */
export const siteDescriptions = {
  en:
    'Acoustic measurement toolkit for Python covering sound level metrology, ' +
    'psychoacoustics, rooms and buildings, vibration, environment and transport, ' +
    'underwater acoustics, electroacoustics and wave simulation, with ' +
    `${totalChecks} conformance checks against ${designations} normative ` +
    `designations and ${sources} further published sources.`,
  es:
    'Biblioteca de medición acústica en Python que abarca la metrología de ' +
    'niveles sonoros, la psicoacústica, las salas y la edificación, la ' +
    'vibración, el medio ambiente y el transporte, la acústica submarina, la ' +
    'electroacústica y la simulación de ondas, con ' +
    `${totalChecks} comprobaciones de conformidad frente a ${designations} ` +
    `designaciones normativas y ${sources} fuentes publicadas adicionales.`,
};

/** The scope sentence in English, for Starlight's own `description`, which has no language form. */
export const siteDescription = siteDescriptions.en;

/**
 * The shorter form, for the `SoftwareApplication` node.
 *
 * jmrp.io describes the same node, under the same `@id`, in its own
 * structured data, from the `summary` of its projects data, and its CI fails
 * when either language here differs from that summary by a character: the
 * wording here and the one there change together, the Spanish included, and
 * the counts with every change to the conformance report.
 */
export const softwareDescriptions = {
  en:
    'Acoustic measurement, analysis and prediction for Python: sound level ' +
    'metrology, psychoacoustics, room and building acoustics, materials, ' +
    'vibration, environmental and transport noise, underwater acoustics, ' +
    'electroacoustics and wave simulation, with ' +
    `${totalChecks} CI-enforced conformance checks across ${domains} domains, ` +
    `against ${designations} normative designations and ${sources} further ` +
    'published sources.',
  es:
    'Medición, análisis y predicción acústica para Python: metrología de ' +
    'niveles sonoros, psicoacústica, acústica de salas y edificación, ' +
    'materiales, vibración, ruido ambiental y de transporte, acústica ' +
    'subacuática, electroacústica y simulación de ondas, con ' +
    `${totalChecks} comprobaciones de conformidad en CI sobre ${domains} dominios, ` +
    `frente a ${designations} designaciones normativas y ${sources} fuentes ` +
    'publicadas adicionales.',
};

/** Every designation the landing page lists in one language, once each. */
const designationsOf = ({ coverage }) => [...new Set(coverage.areas.flatMap((area) => area.standards))];

/**
 * Search keywords: the subject, the language, each area, and every
 * designation implemented. Built from the same source as `featureList` for
 * the same reason.
 *
 * A keyword in words is tagged with its language, the English and the
 * Spanish side by side. A designation is the same in both, "ISO 717-1" is
 * not translated, so one written the same way on both landing pages is
 * given once and untagged; the few the Spanish page writes in its own words,
 * "Anexo 16 OACI" for "ICAO Annex 16", are tagged like the rest. An area
 * whose name says nothing about acoustics on its own gives the keyword its
 * row declares instead.
 */
export const keywords = (() => {
  const written = { en: designationsOf(en), es: designationsOf(es) };
  const shared = written.en.filter((designation) => written.es.includes(designation));
  return [
    tagged('acoustics', 'en'),
    tagged('acústica', 'es'),
    'Python',
    ...LANGUAGES.flatMap((language) =>
      HOME[language].coverage.areas.map((area) => tagged(area.keyword ?? area.name.toLowerCase(), language)),
    ),
    ...shared,
    ...LANGUAGES.flatMap((language) =>
      written[language].filter((designation) => !shared.includes(designation)).map((designation) => tagged(designation, language)),
    ),
  ];
})();

/** The alt text for the social image, kept in step with the current scope. */
export const socialImageAlt =
  'phonometry: standards-conformant acoustic measurement, analysis and prediction for Python';
