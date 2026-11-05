import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const backendPort = process.env.BACKEND_PORT || '5001';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': `http://127.0.0.1:${backendPort}`,
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    restoreMocks: true,
    unstubGlobals: true,
  },
});
