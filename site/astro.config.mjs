import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
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
    starlight({
      title: 'PyOctaveBand',
      customCss: ['./src/styles/katex.css'],
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
