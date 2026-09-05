import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// base: './' —— 构建产物的 JS/CSS 引用使用相对路径，
// 保证部署到任意子路径（如 https://host/stock-tools/）都能正确加载资源
const devBackend = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:5000'

export default defineConfig({
  plugins: [vue()],
  base: './',
  server: {
    port: 5173,
    // 仅开发模式使用：/api 代理到本地后端，地址可用环境变量 VITE_BACKEND_URL 覆盖
    proxy: {
      '/api': {
        target: devBackend,
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
