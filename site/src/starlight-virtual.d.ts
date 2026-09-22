// Ambient types for Starlight's virtual modules.
//
// These modules exist only inside Vite's virtual module graph: Starlight's
// build plugin (vite-plugin-starlight-user-config) synthesises their source
// on the fly, so there is no file on disk for TypeScript to resolve. The
// package itself ships no declarations for them either, since its own
// `.astro` sources are type-checked from within its own repo, never as a
// published `.d.ts`. Header.astro and PageSidebar.astro reach through these
// modules to get at the components a Starlight config may override, so the
// imports stay; this file just tells TypeScript what comes back.
declare module 'virtual:starlight/user-config' {
	import type { StarlightConfig } from '@astrojs/starlight/types';

	const config: StarlightConfig;
	export default config;
}

declare module 'virtual:starlight/components/*' {
	import type { AstroComponentFactory } from 'astro/runtime/server/index.js';

	const Component: AstroComponentFactory;
	export default Component;
}
