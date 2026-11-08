/** CR-11 (D-309, D-310): form LMS Demo gửi qua API thật, trang Phân tích & Cảnh báo, chuyển hướng. */
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

function courseRow(page, code) {
  return page
    .getByRole('table', { name: 'Môn đang học và dữ liệu LMS mới nhất' })
    .locator('tbody tr')
    .filter({ hasText: code });
}

test('thiennhan: 5 môn đang học, tuần 8 của từng môn ở ngày demo 26/10/2026', async ({ page }) => {
  await login(page, 'thiennhan');
  await page.goto('/m11/phan-tich');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Phân tích & Cảnh báo');
  await expect(page.getByRole('heading', { name: 'Cảnh báo học vụ' })).toBeVisible();
  const rows = page
    .getByRole('table', { name: 'Môn đang học và dữ liệu LMS mới nhất' })
    .locator('tbody tr');
  await expect(rows).toHaveCount(5);
  const weeks = {
    CNTT1117: 'Tuần 8 (20/10/2026–26/10/2026)',
    CNTT1140: 'Tuần 8 (22/10/2026–28/10/2026)',
    CNTT1159: 'Tuần 8 (23/10/2026–29/10/2026)',
    CNTT1180: 'Tuần 8 (26/10/2026–01/11/2026)',
    CNTT1188: 'Tuần 8 (21/10/2026–27/10/2026)',
  };
  for (const [code, week] of Object.entries(weeks)) {
    await expect(courseRow(page, code)).toContainText(week);
  }
  await expect(courseRow(page, 'CNTT1159')).toContainText('2/8 buổi');
  await expect(courseRow(page, 'CNTT1188')).toContainText('4/7 đã nộp · 3 quá hạn · 1 nộp muộn');
  for (const old of ['Xu hướng GPA', 'So sánh hai kỳ', 'Đối chiếu chương trình đào tạo']) {
    await expect(page.getByText(old, { exact: true })).toHaveCount(0);
  }
});

test('/m11/canh-bao chuyển sang trang gộp, giữ ?student= và ?semester=', async ({ page }) => {
  await login(page, 'admin');
  await page.goto('/m11/canh-bao?student=NEU-KHMT-001&semester=S4');
  await expect(page).toHaveURL(/\/m11\/phan-tich\?student=NEU-KHMT-001&semester=S4$/);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Phân tích & Cảnh báo');
  await expect(page.getByText(/chỉ có ở kỳ hiện tại/)).toBeVisible();
});

test('admin gửi dữ liệu LMS Demo: số tổng do backend tính, sinh viên thấy ngay', async ({
  page,
}) => {
  await login(page, 'admin');
  await page.goto('/quan-tri/lms-demo');
  await page.locator('#lms-student').selectOption('NEU-KHMT-001');
  await page.locator('#lms-course').selectOption('CNTT1159');
  await expect(page.getByText('Dữ liệu đã gửi của tuần 8')).toBeVisible();
  const session5 = page.getByRole('group', { name: 'Buổi 5 · 02/10/2026' });
  // Bổ sung D-312 (commit đầu CR-13): nhãn "Vắng" thành "Vắng không phép".
  await session5.getByRole('radio', { name: 'Vắng không phép', exact: true }).check();
  const totals = page.locator('.lms-totals');
  await expect(totals).toContainText('Vắng không phép3');
  await page.getByRole('button', { name: 'Gửi sang hệ thống cảnh báo' }).click();
  await expect(page.getByText(/Đã gửi tuần 8 của CNTT1159/)).toBeVisible();

  const api = await page.request.get(
    '/api/lms/snapshots/latest?student_id=NEU-KHMT-001&course_id=CNTT1159',
  );
  const { snapshot } = await api.json();
  expect(snapshot.week.week_no).toBe(8);
  expect(snapshot.summary.absent).toBe(3);

  await login(page, 'thiennhan');
  await page.goto('/m11/phan-tich');
  await expect(courseRow(page, 'CNTT1159')).toContainText('3/8 buổi');
});

test('sinh viên không mở được LMS Demo, API trả 403', async ({ page }) => {
  await login(page, 'thiennhan');
  await page.goto('/quan-tri/lms-demo');
  await expect(page.getByText('Bạn không có quyền xem trang này')).toBeVisible();
  const response = await page.request.get('/api/lms/form-options');
  expect(response.status()).toBe(403);
});

test('axe: LMS Demo và Phân tích & Cảnh báo ở 1440 và 375', async ({ page }) => {
  for (const width of [1440, 375]) {
    await page.setViewportSize({ width, height: width === 375 ? 812 : 1000 });
    await login(page, 'admin');
    await page.goto('/quan-tri/lms-demo');
    await page.locator('#lms-student').selectOption('NEU-KHMT-001');
    await page.locator('#lms-course').selectOption('CNTT1188');
    await expect(page.locator('.lms-totals')).toContainText('Quá hạn chưa nộp3');
    expect(await seriousViolations(page), `lms-demo ${width}`).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      width,
    );
    await login(page, 'thiennhan');
    await page.goto('/m11/phan-tich');
    await expect(courseRow(page, 'CNTT1188')).toBeVisible();
    expect(await seriousViolations(page), `phan-tich ${width}`).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      width,
    );
  }
});
