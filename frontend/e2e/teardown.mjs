/** Xóa thư mục tạm của lần chạy e2e này (CSDL và tệp tải lên), kể cả khi có test đỏ. */
import { rmSync } from 'node:fs';
import { RUN_DIR } from './env.mjs';

export default function teardown() {
  rmSync(RUN_DIR, { recursive: true, force: true });
}
