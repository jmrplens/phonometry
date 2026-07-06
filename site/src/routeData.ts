import { defineRouteMiddleware } from '@astrojs/starlight/route-data';

// Splash (landing) pages don't render a sidebar, which also removes the
// mobile menu button. Force the sidebar data on so the hamburger menu is
// available on mobile; desktop hides the sidebar pane via CSS
// (src/styles/splash-menu.css) to keep the splash layout clean.
export const onRequest = defineRouteMiddleware(({ locals }) => {
  const { starlightRoute } = locals;
  if (starlightRoute?.entry?.data?.template === 'splash') {
    starlightRoute.hasSidebar = true;
  }
});
