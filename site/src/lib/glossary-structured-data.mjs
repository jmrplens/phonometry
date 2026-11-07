/**
 * The glossary's structured data: one `DefinedTermSet` per language, one
 * `DefinedTerm` per entry of src/data/glossary.mjs.
 *
 * It used to be built inside src/components/Glossary.astro. It lives here so
 * that scripts/check-structured-data.test.mjs can hand the check exactly what
 * the page publishes, and see it pass, before anything is built; the check
 * itself reads the built page and never this module.
 *
 * A term is named by its quantity, the words a reader asking about it uses,
 * and the symbol rides along as the alternate name and the code. Named by the
 * symbol alone, as every symbolised entry used to be, the node for LAeq never
 * said "A-weighted equivalent continuous sound pressure level". An entry
 * labelled by a term rather than a symbol has no code, and its alternate name
 * is the alias the entry declares, "PML" for the perfectly matched layer, or
 * none: a label is not an alias, and "Cepstrum and quefrency" names two
 * things.
 *
 * The guide stays an inline node, named and with its address, so a reader of
 * the glossary page alone still learns where the quantity is computed; its
 * `@id` is the article node that page itself publishes, which is what lets a
 * consumer that has read both join them.
 *
 * Written as .mjs with JSDoc so that the test imports it under plain Node.
 */
import { glossary } from '../data/glossary.mjs';
import { basePath, siteUrl } from '../data/site.mjs';
import { plainText } from './maths-text.mjs';

/** The site's root, with its base path and no trailing slash. */
const SITE = `${siteUrl}${basePath}`;

/**
 * A field shared by both languages or given per language, in `lang`.
 *
 * @template T
 * @param {T | { en: T, es: T } | undefined} value The field as the entry stores it.
 * @param {'en' | 'es'} lang The language of the page.
 * @returns {T | undefined} The value in that language.
 */
export const localized = (value, lang) =>
	value !== null && typeof value === 'object' && !Array.isArray(value) ? value[lang] : value;

/**
 * The aliases an entry declares in `lang`, none when it declares none.
 *
 * @param {string | string[] | { en: string | string[], es: string | string[] } | undefined} value
 * @param {'en' | 'es'} lang The language of the page.
 * @returns {string[]} The aliases, in the order the entry gives them.
 */
export const aliasesOf = (value, lang) => {
	const declared = localized(value, lang);
	if (declared === undefined) return [];
	return Array.isArray(declared) ? declared : [declared];
};

/**
 * The glossary's `DefinedTermSet` in one language.
 *
 * @param {'en' | 'es'} lang The language of the page it is published on.
 * @param {(slug: string) => string | undefined} guideTitle The title of the
 *   page at a guide slug in that language; a slug with no page is an error.
 * @returns {object} The JSON-LD document, with its `@context`.
 */
export function glossaryTermSet(lang, guideTitle) {
	const locale = lang === 'es' ? '/es' : '';
	const page = `${SITE}${locale}/reference/glossary/`;
	return {
		'@context': 'https://schema.org',
		'@type': 'DefinedTermSet',
		'@id': `${page}#glossary`,
		name: lang === 'es' ? 'Glosario acústico de phonometry' : 'phonometry acoustic glossary',
		url: page,
		inLanguage: lang,
		hasDefinedTerm: glossary.flatMap((group) =>
			group.terms.map((term) => {
				const title = guideTitle(term.guide);
				if (!title) {
					throw new Error(`glossary: term "${term.id}" points at ${term.guide}, which is not a page in ${lang}`);
				}
				const code = term.symbol ? plainText(term.symbol) : undefined;
				const aliases = aliasesOf(term.alias, lang);
				const alternate = code ?? (aliases.length > 1 ? aliases : aliases[0]);
				const where = [localized(term.standard, lang), localized(term.clause, lang)]
					.filter(Boolean)
					.map(plainText)
					.join(', ');
				const unit = localized(term.unit, lang);
				const unitSentence = unit ? ` ${lang === 'es' ? 'Unidad' : 'Unit'}: ${plainText(unit)}.` : '';
				const guide = `${SITE}${locale}/${term.guide}/`;
				return {
					'@type': 'DefinedTerm',
					'@id': `${page}#${term.id}`,
					name: localized(term.quantity, lang),
					...(alternate === undefined ? {} : { alternateName: alternate }),
					...(code === undefined ? {} : { termCode: code }),
					description:
						`${plainText(localized(term.definition, lang))}${unitSentence} ` +
						`${lang === 'es' ? 'Definida en' : 'Defined in'}: ${where}.`,
					inDefinedTermSet: { '@id': `${page}#glossary` },
					subjectOf: { '@type': 'TechArticle', '@id': `${guide}#article`, name: title, url: guide },
				};
			}),
		),
	};
}
