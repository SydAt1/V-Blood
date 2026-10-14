import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/compounds': 'http://127.0.0.1:8000',
      '/scenarios': 'http://127.0.0.1:8000',
      '/models': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/simulations': 'http://127.0.0.1:8000',
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
  },
})
