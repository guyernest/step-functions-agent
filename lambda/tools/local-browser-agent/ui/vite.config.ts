import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: {
    port: 3030,
    strictPort: true,
    host: 'localhost',
    cors: true,
    watch: {
      // Ignore browser profiles to prevent rebuild loops when sessions are created/updated
      ignored: [
        '**/browser-profiles/**',
        '**/src-tauri/browser-profiles/**',
        '**/python/browser-profiles/**',
        '**/node_modules/**',
        '**/target/**'
      ]
    }
  },
  envPrefix: ['VITE_', 'TAURI_'],
  build: {
    target: ['es2021', 'chrome100', 'safari13'],
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    sourcemap: !!process.env.TAURI_DEBUG,
  },
})
