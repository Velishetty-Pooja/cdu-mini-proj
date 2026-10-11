import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: "https://cdu-mini-proj.onrender.com/",
        changeOrigin: true,
      },
      '/static': {
        target:"https://cdu-mini-proj.onrender.com/",
        changeOrigin: true,
      }
    }
  }
})
