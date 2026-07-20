// Type registration for the custom UI strings added on top of Starlight's
// built-in translations (src/content/i18n/*.json, extended schema in
// src/content.config.ts). Makes `Astro.locals.t('phonometry...')` type-check.
declare namespace StarlightApp {
	interface I18n {
		'phonometry.references.title': string;
		'phonometry.report.download': string;
		'phonometry.video.download': string;
		'phonometry.video.fallback': string;
	}
}
