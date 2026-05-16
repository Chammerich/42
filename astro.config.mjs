// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://42.chammerich.de',

  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'de', 'en'],
    routing: {
      prefixDefaultLocale: true,
      redirectToDefaultLocale: true,
    },
    fallback: {
      de: 'es',
      en: 'es',
    },
  },

  build: {
    format: 'directory',
  },
});
