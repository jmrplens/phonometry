import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';
import mermaid from 'astro-mermaid';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

export default defineConfig({
  site: 'https://jmrplens.github.io',
  base: '/PyOctaveBand',
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeKatex],
  },
  integrations: [
    mermaid({
      theme: 'default',
      autoTheme: true,
    }),
    starlight({
      title: 'PyOctaveBand',
      plugins: [
        starlightLinksValidator({
          errorOnRelativeLinks: false,
          errorOnFallbackPages: false,
        }),
      ],
      lastUpdated: true,
      customCss: ['./src/styles/katex.css', './src/styles/theme-images.css'],
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/jmrplens/PyOctaveBand' },
      ],
      defaultLocale: 'root',
      locales: {
        root: { label: 'English', lang: 'en' },
        es: { label: 'Español', lang: 'es' },
      },
      sidebar: [
        {
          label: 'Start',
          translations: { es: 'Inicio' },
          items: ['getting-started'],
        },
        {
          label: 'Guides',
          translations: { es: 'Guías' },
          items: [
            'guides/filter-banks',
            'guides/weighting',
            'guides/time-weighting',
            'guides/levels',
            'guides/calibration',
            'guides/block-processing',
            'guides/multichannel',
          ],
        },
        {
          label: 'Reference',
          translations: { es: 'Referencia' },
          items: ['reference/api', 'reference/theory', 'reference/why-pyoctaveband'],
        },
      ],
    }),
  ],
});
