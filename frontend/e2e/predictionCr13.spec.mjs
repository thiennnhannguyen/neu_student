/** CR-13 (D-314): bảng 2 cột Môn học · Điểm dự kiến và trang chi tiết môn, qua API thật, ngày demo. */
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { seed } from './env.mjs';
import { login } from './helpers.mjs';

test.beforeEach(() => seed());

async function seriousViolations(page) {
  await page.waitForLoadState('networkidle');
  const { violations } = await new AxeBuilder({ page }).analyze();
  return violations
    .filter((item) => ['serious', 'critical'].includes(item.impact))
    .map((item) => item.id);
}

async function horizontalOverflow(page) {
  return page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
}

const TABLE = 'Môn đang học và điểm dự kiến';
const EXPECTED = [
  ['CNTT1188', '6,78 C+Nguy cơ cao'],
  ['CNTT1159', '8,28 B+Nguy cơ cao'],
  ['CNTT1140', '7,68 BCần chú ý'],
  ['CNTT1117', '7,89 B'],
  ['CNTT1180', '8,98 A'],
];

for (const width of [1440, 375]) {
  test(`${width}px: bảng 2 cột, đúng thứ tự và điểm của 5 môn, axe không lỗi`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await login(page, 'thiennhan');
    await page.goto('/m11/phan-tich');
    const table = page.getByRole('table', { name: TABLE });
    await expect(table.getByRole('columnheader')).toHaveText(['Môn học', 'Điểm dự kiến']);
    const rows = table.locator('tbody tr');
    await expect(rows).toHaveCount(5);
    for (const [index, [code, score]] of EXPECTED.entries()) {
      await expect(rows.nth(index).getByRole('rowheader')).toContainText(code);
      await expect(rows.nth(index).getByRole('cell')).toHaveText(score);
      // Ở 375px vẫn là 2 ô trên một hàng, cùng một dòng.
      const header = await rows.nth(index).getByRole('rowheader').boundingBox();
      const cell = await rows.nth(index).getByRole('cell').boundingBox();
      expect(cell.x).toBeGreaterThan(header.x);
      expect(Math.abs(cell.y - header.y)).toBeLessThan(header.height);
    }
    await expect(page.getByRole('heading', { name: 'Cảnh báo học vụ' })).toBeVisible();
    expect(await seriousViolations(page)).toEqual([]);
    expect(await horizontalOverflow(page)).toBe(0);
  });

  test(`${width}px: bấm cả dòng mở trang chi tiết CNTT1188, axe không lỗi`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await login(page, 'thiennhan');
    await page.goto('/m11/phan-tich');
    const row = page.getByRole('table', { name: TABLE }).locator('tbody tr').first();
    // Bấm vào ô điểm (không phải chữ tên môn): cả dòng bấm được.
    await expect(row.getByRole('cell')).toHaveText('6,78 C+Nguy cơ cao');
    await row.getByRole('cell').click();
    await expect(page).toHaveURL(/\/m11\/phan-tich\/mon\/CNTT1188$/);
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Lập trình Web');
    const summary = page.locator('.prediction-summary');
    await expect(summary).toContainText('6,78C+');
    await expect(summary).toContainText('5,32–8,25');
    await expect(summary).toContainText('Trung bình');
    await expect(summary).toContainText('Nguy cơ cao');
    await expect(summary).toContainText('Thiếu 3/7 bài đã quá hạn');
    const components = page.getByRole('table', { name: 'Thành phần điểm dự kiến' });
    await expect(components).toContainText('10%');
    await expect(components).toContainText('5,37');
    await expect(components).toContainText('7,28');
    await expect(page.locator('.target-list')).toContainText('Đạt C (5,5)4,71');
    await expect(page.locator('.target-list')).toContainText('Đạt A (8,5)Không đạt được');
    await expect(page.getByRole('img', { name: /^Điểm dự kiến theo tuần/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Lộ trình cải thiện – sắp có' })).toBeVisible();
    await expect(
      page.getByText(/Dự kiến chỉ mang tính tham khảo, dựa trên dữ liệu mô phỏng\./),
    ).toBeVisible();
    expect(await seriousViolations(page)).toEqual([]);
    expect(await horizontalOverflow(page)).toBe(0);
  });
}

test('cố vấn được phân công xem qua ?student=, quay lại giữ sinh viên', async ({ page }) => {
  await login(page, 'gv2');
  await page.goto('/m11/phan-tich?student=NEU-KHMT-001');
  await page.getByRole('link', { name: /CNTT1159\s*: điểm dự kiến/ }).click();
  await expect(page).toHaveURL(/\/m11\/phan-tich\/mon\/CNTT1159\?student=NEU-KHMT-001$/);
  await expect(page.locator('.prediction-summary')).toContainText(
    'Vắng 2 buổi không phép – vắng thêm 1 buổi sẽ không được dự thi',
  );
  await page.locator('.back-link').click();
  await expect(page).toHaveURL(/\/m11\/phan-tich\?student=NEU-KHMT-001$/);
});

test('môn không thuộc sinh viên và cố vấn không được phân công: báo lỗi, không lộ dữ liệu', async ({
  page,
}) => {
  await login(page, 'thiennhan');
  await page.goto('/m11/phan-tich/mon/CNTT1165');
  await expect(page.getByText('Không tải được môn học')).toBeVisible();
  await expect(page.locator('.prediction-summary')).toHaveCount(0);
  await login(page, 'gv1');
  const response = await page.request.get(
    '/api/m11/courses/CNTT1188/prediction?student_id=NEU-KHMT-001',
  );
  expect(response.status()).toBe(404);
  await login(page, 'ht1');
  const support = await page.request.get(
    '/api/m11/courses/CNTT1188/prediction?student_id=NEU-KHMT-001',
  );
  expect(support.status()).toBe(403);
});
