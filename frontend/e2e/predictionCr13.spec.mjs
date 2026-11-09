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
  // D-316: CNTT1159 CC 10 − 3 = 7 thay 7,5.
  ['CNTT1159', '8,23 B+Nguy cơ cao'],
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
  // D-315 (CR-13b): từ 768px quay lại bằng đường dẫn phân cấp; liên kết riêng chỉ có ở điện thoại.
  await page
    .getByRole('navigation', { name: 'Vị trí trang' })
    .getByRole('link', { name: 'Phân tích & Cảnh báo' })
    .click();
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

test('CR-13b: đường dẫn phân cấp có tên môn, biểu đồ trục 0–10 có ngưỡng và nhãn tuần', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await login(page, 'gv2');
  await page.goto('/m11/phan-tich/mon/CNTT1188?student=NEU-KHMT-001');
  const trail = page.getByRole('navigation', { name: 'Vị trí trang' });
  await expect(trail.getByRole('listitem')).toHaveText([
    'Tổng quan',
    'Học tập',
    'Phân tích & Cảnh báo',
    'Lập trình Web',
  ]);
  await expect(trail.getByRole('link', { name: 'Phân tích & Cảnh báo' })).toHaveAttribute(
    'href',
    '/m11/phan-tich?student=NEU-KHMT-001',
  );
  // Từ 768px đã có đường dẫn phân cấp: không có liên kết quay lại riêng.
  await expect(page.locator('.back-link')).toBeHidden();
  const plot = page.getByRole('img', { name: /^Điểm dự kiến theo tuần/ });
  const svg = plot.locator('svg.recharts-surface');
  for (const text of ['0', '2', '4', '6', '8', '10', 'T1', 'T8', 'Ngưỡng đạt 4,5', 'Mức C 5,5']) {
    await expect(svg.getByText(text, { exact: true }).first()).toBeVisible();
  }
  await expect(svg.locator('.recharts-line-dot')).toHaveCount(8);
  const box = await plot.boundingBox();
  const block = await page.locator('.weekly-chart').boundingBox();
  expect(Math.abs(box.width - block.width)).toBeLessThan(2);
});

test('D-316: CNTT1159 ghi trừ điểm chuyên cần; 375px có liên kết quay lại', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await login(page, 'thiennhan');
  await page.goto('/m11/phan-tich/mon/CNTT1159');
  const table = page.getByRole('table', { name: 'Thành phần điểm dự kiến' });
  await expect(table).toContainText('Số thật: 10 − 3 (vắng 2 buổi không phép) = 7');
  await expect(page.locator('.prediction-summary')).toContainText('8,23');
  await expect(page.locator('.back-link')).toBeVisible();
  expect(await seriousViolations(page)).toEqual([]);
});
