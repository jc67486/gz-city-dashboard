import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// GitHub Pages 部署在 /仓库名/ 子路径下，生产构建要带 base；
// 本地 dev 仍走根路径，避免 http://localhost:5173/ 打不开
const REPO = 'gz-city-dashboard'

export default defineConfig(({ mode }) => ({
  base: mode === 'production' ? `/${REPO}/` : '/',
  plugins: [vue()],
  server: {
    port: 5173,
    watch: { ignored: ['**/tmp/**', '**/shot/**', '**/dist/**'] },
    proxy: {
      '/api': { target: 'http://127.0.0.1:5001', changeOrigin: true }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          echarts: ['echarts']
        }
      }
    }
  }
}))
