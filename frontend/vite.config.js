import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发模式：/api 代理到本地 Flask 后端 (5000)
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    chunkSizeWarningLimit: 1500,
  },
})
