/**
 * Breadcrumb trails derived from the navigation tree.
 *
 * The trails used to be built by accumulating URL path segments, which is a
 * reasonable guess and mostly wrong here: the old `/guides/` and
 * `/guides/sections/` prefixes, and `/reference/api/<domain>/`, are grouping
 * prefixes rather than routes. That produced
 * 44 distinct `BreadcrumbList` targets that 404, on 414 of 442 pages, and
 * machine-titlecased labels ("Api", "Building") in both locales.
 *
 * `src/data/topics.mjs` already describes the real hierarchy, with a
 * translated label on every group and an explicit `Overview` entry on each
 * group that has a landing page. Reading the trail from there means a crumb
 * exists only where a page exists, the labels are the ones a reader sees in
 * the sidebar, and adding a section keeps the two in step automatically.
 */
import { navigationTree as sidebar } from '../data/topics.mjs';

/** Slug of a sidebar entry, whichever of the two shapes it uses. */
function slugOf(item) {
  if (typeof item === 'string') return item;
  if (item && typeof item === 'object' && typeof item.slug === 'string') return item.slug;
  return undefined;
}

/** Group label in the requested locale, falling back to the English one. */
function labelOf(group, lang) {
  if (lang === 'en') return group.label;
  return group.translations?.[lang] ?? group.label;
}

/**
 * A group is only linkable if it carries a landing page, which the tree
 * expresses as an `Overview` entry (groups themselves cannot be links in
 * Starlight). Convention here: the overview is the group's first item.
 */
function overviewSlugOf(group) {
  for (const item of group.items ?? []) {
    const slug = slugOf(item);
    // Only an explicit `{ slug, label: 'Overview' }` entry counts. A bare
    // string is an ordinary page that happens to be listed first.
    if (slug && typeof item === 'object' && item.label === 'Overview') return slug;
  }
  return undefined;
}

/**
 * slug -> array of ancestor groups, outermost first. Built once at module
 * load and shared by every page render.
 */
const ANCESTORS = new Map();

/**
 * slug -> the tree's own entry for it (a bare slug, or an object with its
 * label and translations), from the same placement ANCESTORS keeps. It names
 * the crumb of a listed page that another page sits under.
 */
const ENTRIES = new Map();

(function walk(items, trail) {
  for (const item of items) {
    const slug = slugOf(item);
    if (slug !== undefined) {
      // A page can legitimately appear twice in the tree; the first placement
      // wins, which keeps the trail stable rather than order-dependent.
      if (!ANCESTORS.has(slug)) {
        ANCESTORS.set(slug, trail);
        ENTRIES.set(slug, item);
      }
      continue;
    }
    if (item && Array.isArray(item.items)) {
      walk(item.items, [...trail, item]);
    }
  }
})(sidebar, []);

/**
 * Build the breadcrumb trail for a page.
 *
 * @param {object} options
 * @param {string} options.slug   Page slug without the locale prefix, e.g. `guides/levels`.
 * @param {string} options.title  Rendered page title, used for the last crumb.
 * @param {'en'|'es'} options.lang
 * @param {string} options.origin Absolute origin, e.g. `https://docs.jmrp.io`.
 * @param {string} options.base   Base path without a trailing slash, e.g. `/phonometry`.
 * @returns {{name: string, item: string}[]} Crumbs, root first, every `item` a real route.
 */
export function breadcrumbsFor({ slug, title, lang, origin, base }) {
  const prefix = `${origin}${base}${lang === 'es' ? '/es' : ''}`;
  const crumbs = [{ name: 'phonometry', item: `${prefix}/` }];

  // A page the tree does not list sits under the nearest route it does: an
  // errata page, `reference/errata/iso-3743`, is one of 96 the registry's
  // index lists and the sidebar does not, and its trail is the index's with
  // the index added, as its address says. Without this its trail skipped
  // straight from the root to the page.
  const parent = ANCESTORS.has(slug) ? undefined : listedParentOf(slug);

  const trail = ANCESTORS.get(parent ?? slug) ?? [];
  for (const group of trail) {
    const overview = overviewSlugOf(group);
    // Groups with no landing page (the two-row "Start" group, the API
    // subgroups) contribute nothing rather than a dead link.
    if (!overview) continue;
    // Skip a group whose landing page is this page: a crumb cannot be its own
    // parent, and the page is about to be appended as the leaf.
    if (overview === slug) continue;
    crumbs.push({ name: labelOf(group, lang), item: `${prefix}/${overview}/` });
  }

  if (parent !== undefined) {
    const item = `${prefix}/${parent}/`;
    // A route that is its group's landing page is already in the trail, under
    // the group's name.
    if (!crumbs.some((crumb) => crumb.item === item)) {
      const entry = ENTRIES.get(parent);
      // The crumb is named as the sidebar names the route. A route listed as
      // a bare slug has no name of its own here, and inventing one from the
      // slug would publish a label no reader ever sees on the site.
      if (typeof entry !== 'object' || typeof entry.label !== 'string') {
        throw new Error(
          `[breadcrumbs] ${slug} is not in the navigation tree, and the route it sits under, ` +
            `${parent}, is listed in src/data/topics.mjs without a label to name its crumb. ` +
            'Give that entry a label (and its translations).',
        );
      }
      crumbs.push({ name: labelOf(entry, lang), item });
    }
  }

  crumbs.push({ name: title, item: `${prefix}/${slug}/` });
  return crumbs;
}

/**
 * The longest route above `slug` that the tree lists, or undefined.
 *
 * @param {string} slug A page slug the tree does not list.
 * @returns {string | undefined}
 */
function listedParentOf(slug) {
  for (let route = slug; route.includes('/'); ) {
    route = route.slice(0, route.lastIndexOf('/'));
    if (ANCESTORS.has(route)) return route;
  }
  return undefined;
}

/** Every slug the navigation tree knows about. Used by the route checks. */
export function knownSlugs() {
  return [...ANCESTORS.keys()];
}
