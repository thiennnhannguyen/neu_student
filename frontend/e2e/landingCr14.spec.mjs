/** CR-14: trang giới thiệu nghề Backend qua API thật (demo-k68), quyền theo vai trò, axe 1440 và 375. */
import { URL } from 'node:url';
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { seed } from './env.mjs';
import { login } from './helpers.mjs';

const DETAIL = '/m12/dinh-huong/nghe/backend-developer';
const PAGE = `${DETAIL}/gioi-thieu`;
const SECTIONS = [
  'Một ngày làm việc',
  'Backend khác Frontend, Full-stack, DevOps ở đâu',
  'Kỹ năng cần có',
  'Học ở NEU (KHMT)',
  'Sản phẩm nên có khi xin thực tập',
  'Thu nhập tham khảo',
  'Câu hỏi thường gặp',
  'Bạn đang ở đâu',
  'Bước tiếp theo',
  'Nguồn',
];

test.beforeEach(() => seed());

async function seriousViolations(page) {
  await page.waitForLoadState('networkidle');
  const { violations } = await new AxeBuilder({ page }).analyze();
  return violations
    .filter((item) => ['serious', 'critical'].includes(item.impact))
    .map((item) => `${item.id}: ${item.nodes.map((node) => node.target).join(' | ')}`);
}

async function horizontalOverflow(page) {
  return page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
}

test('lưới nghề → Backend → Giới thiệu nghề → quay lại; axe ở 1440', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await login(page, 'thiennhan');
  await page.goto('/m12/dinh-huong');
  await page.locator('.career-card', { hasText: 'Lập trình viên Backend' }).click();
  await expect(page).toHaveURL(DETAIL);

  await page.getByRole('link', { name: 'Giới thiệu nghề', exact: true }).click();
  await expect(page).toHaveURL(PAGE);
  await expect(
    page.getByRole('heading', { level: 1, name: 'Lập trình viên Backend' }),
  ).toBeVisible();
  await expect(page.getByRole('heading', { level: 2 })).toHaveText(SECTIONS);
  await expect(page.getByRole('navigation', { name: 'Mục lục trang' })).toBeVisible();
  await expect(page.getByText(/Mô-đun tiếp theo nên làm bài kiểm tra:/)).toBeVisible();
  const source = page.getByRole('link', { name: /Backend Developer là gì/ });
  await expect(source).toHaveAttribute('target', '_blank');
  await expect(source).toHaveAttribute('rel', 'noopener noreferrer');
  expect(await seriousViolations(page)).toEqual([]);

  await page.getByRole('link', { name: 'Quay lại trang nghề' }).click();
  await expect(page).toHaveURL(DETAIL);
  await expect(page.getByRole('link', { name: 'Giới thiệu nghề', exact: true })).toBeVisible();
});

test('375px: không tràn ngang, mục lục ẩn, bảng so sánh cuộn trong khung; axe', async ({
  page,
}) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await login(page, 'thiennhan');
  await page.goto(PAGE);

  await expect(
    page.getByRole('heading', { level: 1, name: 'Lập trình viên Backend' }),
  ).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'Mục lục trang' })).toBeHidden();
  await expect(page.getByRole('region', { name: 'Bảng so sánh, cuộn ngang được' })).toBeVisible();
  expect(await horizontalOverflow(page)).toBe(0);
  expect(await seriousViolations(page)).toEqual([]);
});

test('nút Làm bài kiểm tra mô-đun tiếp theo mở đúng mô-đun ở tab Khung năng lực', async ({
  page,
}) => {
  await login(page, 'thiennhan');
  await page.goto(PAGE);
  await page.getByRole('link', { name: 'Làm bài kiểm tra mô-đun tiếp theo' }).click();

  await expect(page).toHaveURL(/tab=framework#module-\d+$/);
  const order = new URL(page.url()).hash.replace('#module-', '');
  await expect(page.locator(`#module-${order}`)).toBeFocused();
});

test('nhân viên hỗ trợ xem được trang, không có phần cá nhân hóa', async ({ page }) => {
  await login(page, 'ht1');
  await page.goto(PAGE);

  await expect(
    page.getByRole('heading', { level: 1, name: 'Lập trình viên Backend' }),
  ).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Bạn đang ở đâu' })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Về trang chủ' })).toBeVisible();
});

test('nghề chưa có nội dung: không có nút ở trang nghề, mở thẳng đường dẫn thì Đang cập nhật', async ({
  page,
}) => {
  await login(page, 'thiennhan');
  await page.goto('/m12/dinh-huong/nghe/frontend-developer');
  await expect(
    page.getByRole('heading', { level: 1, name: 'Lập trình viên Frontend' }),
  ).toBeVisible();
  await expect(page.getByRole('link', { name: 'Giới thiệu nghề', exact: true })).toHaveCount(0);

  await page.goto('/m12/dinh-huong/nghe/frontend-developer/gioi-thieu');
  await expect(page.getByRole('heading', { name: 'Đang cập nhật' })).toBeVisible();
});
