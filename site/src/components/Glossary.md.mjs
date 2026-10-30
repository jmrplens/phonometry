/**
 * Glossary: every quantity of src/data/glossary.mjs, group by group, as the
 * page lists them.
 *
 * Kept: each group under its heading, and each term as one list item: its
 * notation (TeX kept in `$...$`, as the data writes it) or its name, the
 * qualifier that tells apart two entries sharing a symbol, the one-sentence
 * definition, the unit, the standard and clause that define it, and the
 * guide that computes it, linked by that guide's own title as the page links
 * it. These are the fields the page's card shows, and only those.
 *
 * A list rather than a table, although the page once was five-column tables:
 * several definitions carry TeX with a bar in it (`$|G_{xy}|^2$`), which a
 * Markdown table reads as a column break, and escaped as `\|` it would reach
 * a TeX reader as a double bar, a different symbol.
 *
 * Dropped: the symbol index above the groups, which links each letter's
 * meanings to their cards on the same page. A reader of the copy finds a
 * symbol by searching the text, and the copy has no cards to link to. Also
 * dropped: any field of a term that the card does not show, such as a name or
 * an alias the data keeps for the structured data alone. The copy says what
 * the page says, no more.
 */
import { glossary } from '../data/glossary.mjs';
import { pageTitle } from '../lib/agent-md/content.mjs';
import { bracketText, line } from '../lib/agent-md/markdown-table.mjs';
import { markdownFor } from '../lib/agent-md/types.mjs';

/** The words around a term, in each language. */
const WORDS = {
  en: { unit: 'Unit', definedIn: 'Defined in', guide: 'Guide' },
  es: { unit: 'Unidad', definedIn: 'Definida en', guide: 'Guía' },
};

/**
 * A field shared by both languages or given per language.
 *
 * @param {string | { en: string, es: string } | undefined} value
 * @param {'en' | 'es'} lang
 * @returns {string}
 */
const localized = (value, lang) => line(value === undefined ? '' : typeof value === 'string' ? value : value[lang]);

/** A sentence, closed with a full stop when it has no closing mark. */
const sentence = (text) => (!text || /[.!?]$/u.test(text) ? text : `${text}.`);

/**
 * One term as a list item, with the fields its card shows and no other.
 *
 * @param {import('../data/glossary.mjs').GlossaryTerm} term
 * @param {'en' | 'es'} lang
 * @param {{ title: string, url: string }} [guide]  The guide that computes it, when it is a page.
 * @returns {string}
 */
export function termItem(term, lang, guide) {
  const words = WORDS[lang];
  const label = term.symbol || localized(term.name, lang) || term.id;
  const qualifier = localized(term.qualifier, lang);
  const unit = localized(term.unit, lang);
  const definition = localized(term.definition, lang);
  const lead = `**${label}**${qualifier ? ` (${qualifier})` : ''}`;
  const where = [localized(term.standard, lang), localized(term.clause, lang)].filter(Boolean).join(', ');
  const after = [unit && `${words.unit}: ${sentence(unit)}`, where && `${words.definedIn}: ${sentence(where)}`];
  const link = guide ? ` ${words.guide}: [${bracketText(guide.title)}](${guide.url}).` : '';
  return `- ${lead}: ${[sentence(definition), ...after.filter(Boolean)].join(' ')}${link}`;
}

export default markdownFor({
  tag: 'Glossary',
  props: ['lang'],
  toMarkdown(node, ctx) {
    const lang = ctx.attr(node, 'lang') === 'es' ? 'es' : 'en';
    if (lang !== ctx.lang) ctx.issue(node, `Glossary lang="${lang}" on a page in ${ctx.lang}`);
    const locale = lang === 'es' ? 'es/' : '';
    return glossary
      .map((group) => {
        const items = group.terms.map((term) => {
          let guide;
          if (term.guide) {
            const title = pageTitle(`${locale}${term.guide}`);
            if (title) guide = { title, url: ctx.site.url(`/${locale}${term.guide}/`) };
            else ctx.issue(node, `glossary term "${term.id}" points at ${term.guide}, which is not a page in ${lang}`);
          }
          return termItem(term, lang, guide);
        });
        return `${ctx.heading(2, line(group.label[lang]))}\n\n${items.join('\n')}`;
      })
      .join('\n\n');
  },
});
