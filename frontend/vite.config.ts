import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  return {
    plugins: [react()],
    base: env.VITE_APP_BASE_PATH?.trim() || '/',
    server: {
      port: 5173,
      strictPort: true,
    },
  }
})
