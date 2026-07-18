import { defineRouteMiddleware } from '@astrojs/starlight/route-data';

export const onRequest = defineRouteMiddleware(({ locals }) => {
  const { starlightRoute } = locals;
  if (!starlightRoute) return;

  // Splash (landing) pages don't render a sidebar, which also removes the
  // mobile menu button. Force the sidebar data on so the hamburger menu is
  // available on mobile; desktop hides the sidebar pane via CSS
  // (src/styles/splash-menu.css) to keep the splash layout clean.
  if (starlightRoute.entry?.data?.template === 'splash') {
    starlightRoute.hasSidebar = true;
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
