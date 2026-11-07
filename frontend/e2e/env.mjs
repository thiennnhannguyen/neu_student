/** CSDL, thư mục tệp và cấu hình riêng cho e2e, không đụng CSDL của `make dev`. */
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

export const PORT = process.env.E2E_PORT || '8100';
export const BACKEND = resolve(import.meta.dirname, '../../backend');
export const PYTHON = process.env.E2E_PYTHON || join(BACKEND, '.venv/bin/python');

export const SERVER_ENV = {
  ...process.env,
  APP_CONFIG: 'local-prod',
  SESSION_COOKIE_SECURE: 'false',
  SECRET_KEY: 'e2e-only',
  DATABASE_URL: `sqlite:///${join(tmpdir(), 'neu-student-e2e.db')}`,
  UPLOAD_DIR: join(tmpdir(), 'neu-student-e2e-uploads'),
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
