import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    // In production, VITE_API_URL will be an empty string, making API calls relative.
    // In development, it will be undefined, and the config.js will fallback to localhost.
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.NODE_ENV === 'production' ? '' : undefined)
  }
})
