import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
// `vitest/config` re-exports Vite's defineConfig with the `test` field
// typed, so this one config file covers both Vite and Vitest.
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    proxy: {
      // Keeps the browser talking to a single origin in dev (no CORS setup
      // needed). Docker Compose's dev overlay points this at the `api`
      // service by container name; bare `npm run dev` on the host falls
      // back to localhost.
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    watch: {
      // Docker Desktop's bind-mount filesystem doesn't propagate native
      // file-change events into the container (confirmed by testing: edits
      // on the host never triggered HMR without this), so fall back to
      // polling - only set by the Docker dev overlay, never for bare
      // `npm run dev` on the host, where native events work fine.
      usePolling: process.env.VITE_USE_POLLING === 'true',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
