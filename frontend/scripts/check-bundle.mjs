/* global console */
// Kiểm tra bản build production: không có styleguide, không có mật khẩu mẫu.
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import process from 'node:process';

const ASSETS = join(process.cwd(), 'dist', 'assets');
const FORBIDDEN = [
  'Hệ thống thiết kế NEU 2026',
  'dev/styleguide',
  'StyleguidePage',
  'dev/illustrations',
  'IllustrationsSheet',
  'Demo@12345',
];
// Dòng bắt buộc ở mọi trang có logo (AGENTS.md); D-305 đã bỏ badge "Dữ liệu mẫu".
const REQUIRED = 'không phải hệ thống chính thức';

if (!existsSync(ASSETS)) {
  console.error('Chưa có dist/assets. Chạy npm run build trước.');
  process.exit(1);
}
const files = readdirSync(ASSETS).filter((name) => name.endsWith('.js'));
const sources = files.map((name) => [name, readFileSync(join(ASSETS, name), 'utf8')]);
const problems = sources.flatMap(([name, source]) =>
  FORBIDDEN.filter((text) => source.includes(text)).map((text) => `${name}: có "${text}"`),
);
// Không thấy nội dung bắt buộc nghĩa là đang quét nhầm chỗ, kiểm tra không còn ý nghĩa.
if (!sources.some(([, source]) => source.includes(REQUIRED))) {
  problems.push(`Không thấy "${REQUIRED}" trong ${files.length} file JS.`);
}
if (problems.length > 0) {
  console.error(problems.join('\n'));
  process.exit(1);
}
console.log(`check:bundle OK: ${files.length} file JS, không có nội dung cấm.`);
