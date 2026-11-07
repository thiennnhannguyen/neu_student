import { defineConfig } from '@playwright/test';
import { PORT } from './e2e/env.mjs';

const baseURL = `http://localhost:${PORT}`;

// Một worker: các kịch bản seed lại cùng một CSDL. Không chạy lại tự động để không che lỗi chập chờn.
export default defineConfig({
  testDir: './e2e',
  testMatch: '*.spec.mjs',
  workers: 1,
  retries: 0,
  timeout: 60000,
  reporter: [['list']],
  use: { baseURL, viewport: { width: 1440, height: 1000 }, trace: 'retain-on-failure' },
  webServer: {
    command: 'node e2e/server.mjs',
    url: `${baseURL}/api/health`,
    reuseExistingServer: false,
    timeout: 120000,
  },
});
