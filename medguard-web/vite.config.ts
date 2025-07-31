import { fileURLToPath, URL } from 'node:url'
import { resolve, dirname } from 'node:path'
import tailwindcss from '@tailwindcss/vite'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
// import VueI18nPlugin from '@intlify/unplugin-vue-i18n/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    vue(),
    vueDevTools(),
    // VueI18nPlugin({
    //   // locale messages resource pre-compile option
    //   include: resolve(dirname(fileURLToPath(import.meta.url)), './src/locales/**'),
    // }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      }
    }
  },
  define: {
    // Vue I18n build feature flags
    __VUE_I18N_FULL_INSTALL__: 'true',
    __VUE_I18N_LEGACY_API__: 'false', // Composition API mode
    __INTLIFY_DROP_MESSAGE_COMPILER__: 'false' // Keep message compiler for inline messages
  }
})
