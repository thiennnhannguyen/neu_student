import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { seed } from './env.mjs';
import { login } from './helpers.mjs';

const PAGES = [
  ['demo05', '/', 'Tổng quan'],
  ['demo05', '/ho-so', 'Hồ sơ'],
  ['demo05', '/m11/ket-qua', 'Kết quả'],
  ['demo05', '/m11/phan-tich', 'Phân tích'],
  ['demo05', '/m11/canh-bao', 'Cảnh báo'],
  ['demo05', '/m12/dinh-huong', 'Định hướng nghề'],
  ['demo05', '/m12/dinh-huong/nghe/ai-engineer', 'Chi tiết nghề'],
  ['demo05', '/m12/ke-hoach', 'Kế hoạch học tập'],
  ['demo05', '/m12/yeu-cau-ho-tro', 'Yêu cầu hỗ trợ'],
  ['gv2', '/m12/duyet-minh-chung', 'Duyệt minh chứng'],
];

async function seriousViolations(page) {
  await page.waitForLoadState('networkidle');
  const { violations } = await new AxeBuilder({ page }).analyze();
  return violations
    .filter((item) => ['serious', 'critical'].includes(item.impact))
    .map((item) => ({
      id: item.id,
      impact: item.impact,
      nodes: item.nodes.map((node) => `${node.target.join(' ')} ${node.any[0]?.message ?? ''}`),
    }));
}

test.beforeAll(() => seed());

test('axe: /login', async ({ page }) => {
  await page.goto('/login');
  expect(await seriousViolations(page)).toEqual([]);
});

for (const [username, path, name] of PAGES) {
  test(`axe: ${name} (${username})`, async ({ page }) => {
    await login(page, username);
    await page.goto(path);
    expect(await seriousViolations(page)).toEqual([]);
  });
}
