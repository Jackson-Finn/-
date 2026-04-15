import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

function vendorChunk(id) {
  if (!id.includes('node_modules')) {
    return null
  }

  if (id.includes('/echarts/')) {
    return 'charts'
  }

  if (id.includes('/zrender/')) {
    return 'charts-renderer'
  }
  
  return null
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      vue(),
      Components({
        dts: false,
        resolvers: [ElementPlusResolver({ importStyle: 'css' })]
      })
    ],
    server: {
      host: '0.0.0.0',
      port: Number(env.VITE_PORT || 5173),
      proxy: {
        '/api': {
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true
        },
        '/health': {
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true
        }
      }
    },
    build: {
      chunkSizeWarningLimit: 900,
      rollupOptions: {
        output: {
          manualChunks(id) {
            return vendorChunk(id)
          }
        }
      }
    }
  }
})
