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
    head: {
      htmlAttrs: {
        lang: 'zh-Hant',
      },
      title: 'しゆ。Song List',
      meta: [
        { 'http-equiv': 'X-UA-Compatible', content: 'IE=edge' },
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'apple-mobile-web-app-title', content: '', },
        { property: 'og:url', content: 'https://redfire29.github.io/shiyu-song-list/' },
        { property: 'og:site_name', content: 'しゆ。Song List' },
      ],
      link: [
        { rel: 'canonical', href: 'https://redfire29.github.io/shiyu-song-list/' },
        // { rel: 'icon', type: 'image/png', href: '/favicon-96x96.png', sizes: '96x96', },
        // { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg', },
        // { rel: 'shortcut icon', href: '/favicon.ico', },
        // { rel: 'apple-touch-icon', sizes: '180x180', href: '/apple-touch-icon.png', },
        // { rel: 'manifest', href: '/site.webmanifest', },
      ],
      script: [],
    }
  },
  routeRules: {
    '/': { prerender: true }
  }
})
