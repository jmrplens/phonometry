import { defineRouteMiddleware, type StarlightRouteData } from '@astrojs/starlight/route-data';
import { getCollection, type CollectionEntry } from 'astro:content';
import { englishTwin, isApiRoute, isFallbackRoute } from './lib/fallback-routes.mjs';
import { hasMarkdownCopy, markdownCopyPath, routeOf } from './lib/page-markdown.mjs';

const BASE = (import.meta.env.BASE_URL ?? '/').replace(/\/$/, '');

/**
 * The routes `scripts/emit-page-markdown.mjs` publishes a markdown copy for:
 * one per file in the docs collection, minus the splash pages.
 *
 * Membership is what decides, rather than the address of the page, because the
 * two do not agree everywhere. Starlight gives every English page a route in
 * the other locale and serves the English entry there when no translation
 * exists, which is how the whole generated API reference is reachable under
 * `/es/`; those routes have no file, so no copy is written for them. Astro's
 * own synthesised 404 entry is not in the collection either. Reading the copy
 * off the entry that is actually being rendered therefore hands a reader on a
 * fallback page the markdown of the very text in front of them, and offers
 * nothing at all where nothing was written.
 */
const published = new Set(
  (await getCollection('docs'))
    // Astro reports the collection root's index as `index` while Starlight
    // hands the same page the empty id, so both sides go through the one rule
    // the generator uses (src/lib/page-markdown.mjs) before they are compared.
    .map((entry: CollectionEntry<'docs'>) => routeOf(entry.id))
    .filter(hasMarkdownCopy),
);

type SidebarEntry = StarlightRouteData['sidebar'][number];

/**
 * The head of an API page, as src/lib/fallback-routes.mjs says it should be.
 *
 * Starlight writes a self canonical, an `og:url` and an hreflang link per
 * locale plus `x-default` on every route, its fallback routes included
 * (utils/head.ts), so the Spanish copy of an English API page claimed to be a
 * Spanish page of its own. Here the Spanish copy names the English page in its
 * canonical and its `og:url`, and both sides of the pair lose their hreflang
 * links. Every other page keeps Starlight's head as it is.
 *
 * The rule is keyed on the address, and Starlight's own flag has to agree with
 * it: a translated Spanish API page, or an untranslated page anywhere else,
 * would be served with a head that misdescribes it, so either one stops the
 * build here rather than shipping.
 */
function declareFallback(route: StarlightRouteData): void {
  const id = route.id;
  // Absent rather than false on the routes that are no translation at all, the
  // 404 among them.
  const fallback = route.isFallback === true;
  if (fallback !== isFallbackRoute(id)) {
    throw new Error(
      `${id}: Starlight ${fallback ? 'serves it as fallback content' : 'has a translation of it'}, ` +
        'and src/lib/fallback-routes.mjs says the opposite. The canonical, hreflang and sitemap ' +
        'rules there assume the Spanish API reference is the only untranslated subtree.',
    );
  }
  if (!isApiRoute(id)) return;
  route.head = route.head.filter(
    (entry) => !(entry.tag === 'link' && entry.attrs?.rel === 'alternate' && entry.attrs?.hreflang),
  );
  if (!fallback) return;
  for (const entry of route.head) {
    if (entry.tag === 'link' && entry.attrs?.rel === 'canonical' && typeof entry.attrs.href === 'string') {
      entry.attrs.href = englishTwin(entry.attrs.href, BASE);
    }
    if (entry.tag === 'meta' && entry.attrs?.property === 'og:url' && typeof entry.attrs.content === 'string') {
      entry.attrs.content = englishTwin(entry.attrs.content, BASE);
    }
  }
}

/** Every link in a sidebar tree, at any depth. */
function* sidebarLinks(entries: SidebarEntry[]): Generator<Extract<SidebarEntry, { type: 'link' }>> {
  for (const entry of entries) {
    if (entry.type === 'link') yield entry;
    else yield* sidebarLinks(entry.entries);
  }
}

/**
 * Trailing slashes and percent-escapes out of the way, for comparing routes.
 * A stray `%` is not a reason to fail a page render, so a href that will not
 * decode is compared as it came.
 */
function normalizeRoute(href: string): string {
  let decoded = href;
  try {
    decoded = decodeURI(href);
  } catch {
    // Not valid percent-encoding: compare the raw string.
  }
  return decoded.replace(/\/+$/, '');
}

export const onRequest = defineRouteMiddleware(({ locals, url }) => {
  const { starlightRoute } = locals;
  if (!starlightRoute) return;

  // Starlight marks the current page on the first sidebar entry that matches
  // it and stops there (utils/navigation.ts, `getSidebarCurrentEntry`), which
  // assumes a page is listed once. A page can be listed twice here on purpose:
  // the reference index is the landing row of its own topic and the way back
  // to the whole table from inside every domain's API group, so on that page
  // the mark lands on a copy in a topic the reader is not in, and the topic
  // they are in shows 162 rows with none of them theirs. The topics plugin has
  // narrowed the sidebar to the current topic by now (it registers its
  // middleware with `order: 'pre'`), so this is the tree the reader will see:
  // if nothing in it is current, mark the row that points at this page.
  const sidebar = starlightRoute.sidebar ?? [];
  const links = [...sidebarLinks(sidebar)];
  if (links.length > 0 && !links.some((link) => link.isCurrent)) {
    const here = normalizeRoute(url.pathname);
    const match = links.find((link) => normalizeRoute(link.href) === here);
    if (match) {
      match.isCurrent = true;
      // Starlight paginated over a tree it thought this page was not in, so
      // the neighbours it picked are two rows of a table the reader is not
      // reading in order, and following one swaps the sidebar under them.
      // Pagination.astro drops a card that leaves the topic; these do not
      // leave it, they are simply not this page's neighbours.
      starlightRoute.pagination.prev = undefined;
      starlightRoute.pagination.next = undefined;
    }
  }

  // Where this page's markdown copy is, or undefined if it has none. Read by
  // Head.astro for the `rel="alternate"` link and by PageActions.astro, which
  // renders nothing without it.
  const route = routeOf(starlightRoute.entry?.id ?? '');
  starlightRoute.markdownCopy = published.has(route)
    ? markdownCopyPath(route, BASE)
    : undefined;

  // The API reference is generated from the package docstrings, so its pages
  // have no hand-editable source: an "Edit page" link there would invite web
  // edits that the next regeneration silently discards. The prose that a
  // reader could usefully fix lives in the docstrings, not in these files.
  if (isApiRoute(starlightRoute.entry?.id ?? '')) {
    starlightRoute.editUrl = undefined;
  }

  declareFallback(starlightRoute);

  // Open Graph names a locale as language_TERRITORY. Starlight writes the bare
  // language (`en`, `es`) and Head.astro writes the full form next to its
  // alternate, so every page carried two `og:locale` tags that disagreed. The
  // full form is the one the protocol defines, and it is Head.astro's.
  starlightRoute.head = starlightRoute.head.filter(
    (entry) => !(entry.tag === 'meta' && entry.attrs?.property === 'og:locale'),
  );

  // Starlight builds a splash page without a sidebar, which also removes the
  // mobile menu button. Turn it on so the pane exists: what renders in it is
  // the topic list, which is the whole navigation a landing page needs, and
  // the same list a reader meets on every other page
  // (src/components/Sidebar.astro). The tree is empty because a landing page
  // belongs to no topic and there is no other tree to show.
  if (starlightRoute.entry?.data?.template === 'splash') {
    starlightRoute.hasSidebar = true;
    starlightRoute.sidebar = [];
  }

  // The unified bibliography (frontmatter `references`, rendered by the
  // MarkdownContent override) is injected after the markdown pipeline, so its
  // heading never reaches the generated table of contents. Append the entry
  // here to keep "On this page" complete; slug and heading id must match
  // src/components/References.astro.
  if (starlightRoute.entry?.data?.references?.length && starlightRoute.toc) {
    starlightRoute.toc.items.push({
      depth: 2,
      slug: 'references',
      text: locals.t('phonometry.references.title'),
      children: [],
    });
  }
});
