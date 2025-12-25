// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss'],
  tailwindcss: {
    cssPath: [
      '~/assets/css/main.css',
      {
        injectPosition: 'last'
      },
    ],
  },
  app: {
    baseURL: '/shiyu-song-list/', // 例如 '/my-music-list/'，如果是主域名則用 '/'
    buildAssetsDir: 'assets',
  },
  routeRules: {
    '/': { prerender: true }
  }
})
