import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';

const backendPort = process.env.BACKEND_PORT || '5001';

export default defineConfig(({ mode }) => {
  // Mặc định có ở dev, không có ở production. Giá trị cố định lúc build nên khi tắt,
  // hộp tài khoản demo và mật khẩu demo bị loại hẳn khỏi bundle. Test tự đặt biến này.
  const showDemo = loadEnv(mode, process.cwd(), '').VITE_SHOW_DEMO_ACCOUNTS;
  const define = process.env.VITEST
    ? {}
    : {
        'import.meta.env.VITE_SHOW_DEMO_ACCOUNTS': JSON.stringify(
          showDemo ?? String(mode !== 'production'),
        ),
      };

  return {
    plugins: [react()],
    define,
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
      unstubEnvs: true,
    },
  };
});
