/** CSDL, thư mục tệp và cấu hình riêng cho e2e, không đụng CSDL của `make dev`. */
import { execFileSync } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

export const PORT = process.env.E2E_PORT || '8100';
export const BACKEND = resolve(import.meta.dirname, '../../backend');
export const PYTHON = process.env.E2E_PYTHON || join(BACKEND, '.venv/bin/python');

// Mỗi lần chạy e2e một thư mục tạm mới: lần chạy ở cây khác (migration khác) không dẫm lên CSDL này.
// Tiến trình chính của Playwright tạo thư mục khi nạp cấu hình; server e2e và các worker kế thừa
// E2E_RUN_DIR nên cùng dùng một CSDL. globalTeardown (e2e/teardown.mjs) xóa thư mục khi chạy xong.
if (!process.env.E2E_RUN_DIR) {
  process.env.E2E_RUN_DIR = mkdtempSync(join(tmpdir(), 'neu-student-e2e-'));
}
export const RUN_DIR = process.env.E2E_RUN_DIR;

export const SERVER_ENV = {
  ...process.env,
  APP_CONFIG: 'local-prod',
  SESSION_COOKIE_SECURE: 'false',
  SECRET_KEY: 'e2e-only',
  DATABASE_URL: `sqlite:///${join(RUN_DIR, 'e2e.db')}`,
  UPLOAD_DIR: join(RUN_DIR, 'uploads'),
  // D-309: ngày demo cố định, mọi môn của thiennhan đang ở tuần 8 (dữ liệu LMS mẫu là "tuần này").
  DEMO_TODAY: '2026-10-26',
};

function flask(...args) {
  execFileSync(PYTHON, ['-m', 'flask', '--app', 'app', ...args], {
    cwd: BACKEND,
    env: SERVER_ENV,
    stdio: 'pipe',
  });
}

export function migrate() {
  flask('db', 'upgrade');
}

export function seed(profile = 'demo-k68') {
  flask('seed', '--reset', '--profile', profile);
}
