/** Chạy đúng cách `make prod-local` chạy: bản build và API ở 1 cổng qua gunicorn. */
import { spawn } from 'node:child_process';
import { BACKEND, migrate, PORT, PYTHON, seed, SERVER_ENV } from './env.mjs';

migrate();
seed();
const server = spawn(
  PYTHON,
  ['-m', 'gunicorn', '--workers', '1', '--bind', `127.0.0.1:${PORT}`, 'app:create_app()'],
  { cwd: BACKEND, env: SERVER_ENV, stdio: 'inherit' },
);
for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => server.kill(signal));
}
server.on('exit', (code) => process.exit(code ?? 0));
