/** CR-06: trang Kết quả của thiennhan – dòng Tổng kết học kì, cột Chi tiết, không còn nút Học lại. */
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { seed } from './env.mjs';
import { login } from './helpers.mjs';

test.beforeEach(() => seed());

const vn = (value) => (value === null ? '—' : String(value).replace('.', ','));

test('S1–S5: dòng tổng kết khớp API, kỳ chưa có điểm vẫn có dòng tổng kết nhưng để trống', async ({
  page,
}) => {
  await login(page, 'thiennhan');
  for (const semester of ['S1', 'S2', 'S3', 'S4', 'S5']) {
    const api = await page.request.get(`/api/m11/grades?semester_id=${semester}&page_size=1`);
    const summary = (await api.json()).semester_summary;
    await page.goto(`/m11/ket-qua?semester=${semester}`);
    await expect(page.locator('.ui-table tbody tr').first()).toBeVisible();
    const footer = page.locator('.ui-table tfoot tr');
    await expect(footer.locator('th')).toHaveText('Tổng kết học kì');
    if (summary.credits === 0) {
      await expect(footer.locator('td[data-label="Tín chỉ"]')).toHaveText('');
      await expect(footer.locator('td[data-label="Điểm hệ 10"]')).toHaveText('');
      await expect(footer.locator('td[data-label="Hệ 4"]')).toHaveText('');
      continue;
    }
    await expect(footer.locator('td[data-label="Tín chỉ"]')).toHaveText(String(summary.credits));
    await expect(footer.locator('td[data-label="Điểm hệ 10"]')).toHaveText(vn(summary.score_10));
    await expect(footer.locator('td[data-label="Hệ 4"]')).toHaveText(vn(summary.grade_4));
  }
});

test('CR-09 (D-307): HK1 2026-2027 có đúng 5 môn đang học, 3 tín chỉ, không điểm, không tick đạt', async ({
  page,
}) => {
  await login(page, 'thiennhan');
  await page.goto('/m11/ket-qua?semester=S5');
  const rows = page.locator('.ui-table tbody tr');
  await expect(rows).toHaveCount(5);
  const codes = await rows.locator('td[data-label="Mã môn"]').allInnerTexts();
  expect(codes.map((code) => code.trim()).sort()).toEqual([
    'CNTT1117',
    'CNTT1140',
    'CNTT1159',
    'CNTT1180',
    'CNTT1188',
  ]);
  expect(await rows.locator('td[data-label="Tín chỉ"]').allInnerTexts()).toEqual(
    Array(5).fill('3'),
  );
  // Trạng thái chỉ bằng icon có tên đọc được (CR-04); không môn nào có icon "Đạt" (R6).
  await expect(rows.getByRole('img', { name: 'Đang học', exact: true })).toHaveCount(5);
  await expect(rows.getByRole('img', { name: 'Đạt', exact: true })).toHaveCount(0);
  for (const label of ['Điểm hệ 10', 'Điểm chữ', 'Hệ 4']) {
    const cells = await rows.locator(`td[data-label="${label}"]`).allInnerTexts();
    expect(
      cells.every((text) => ['', '—'].includes(text.trim())),
      label,
    ).toBe(true);
  }
});

test('môn học lại trông như dòng thường; Chi tiết mở bảng điểm thành phần của 2 lần học, khớp API', async ({
  page,
}) => {
  await login(page, 'thiennhan');
  await page.goto('/m11/ket-qua?semester=S4');
  const table = page.locator('.ui-table');
  await expect(table.getByText('Cấu trúc dữ liệu và giải thuật')).toBeVisible();
  await expect(table.getByRole('button', { name: /Học lại/ })).toHaveCount(0);

  const toggle = page.getByRole('button', {
    name: 'Chi tiết Cấu trúc dữ liệu và giải thuật (TIHT1101)',
  });
  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  const history = page.getByRole('region', {
    name: 'Chi tiết học phần: TIHT1101 - Cấu trúc dữ liệu và giải thuật',
  });
  const headers = history.locator('thead th');
  await expect(headers).toHaveCount(6);
  await expect(headers.nth(3)).toContainText('Điểm lần 1');
  await expect(headers.nth(3)).toContainText('HK1 2025-2026');
  await expect(headers.nth(4)).toContainText('HK2 2025-2026');
  const api = await page.request.get('/api/m11/grades/TIHT1101/attempts');
  const items = (await api.json()).items;
  const vn = (value) => String(Number(value)).replace('.', ',');
  const rows = history.locator('tbody tr');
  await expect(rows).toHaveCount(3);
  for (const [index, key] of ['attendance_score', 'midterm_score', 'final_score'].entries()) {
    const cells = rows.nth(index).locator('td');
    await expect(cells.nth(3)).toHaveText(vn(items[0].component_scores[key]));
    await expect(cells.nth(4)).toHaveText(vn(items[1].component_scores[key]));
    await expect(cells.nth(5)).toHaveText('');
  }
  await expect(history.locator('tfoot')).toHaveCount(0);
  await toggle.click();
  await expect(history).toBeHidden();
});

test('axe: Kết quả có dòng tổng kết và hàng chi tiết đang mở, 1440 và 375', async ({ page }) => {
  await login(page, 'thiennhan');
  for (const width of [1440, 375]) {
    await page.setViewportSize({ width, height: width === 375 ? 812 : 1000 });
    await page.goto('/m11/ket-qua?semester=S4');
    await page
      .getByRole('button', { name: /^Chi tiết / })
      .first()
      .click();
    await page.waitForLoadState('networkidle');
    const { violations } = await new AxeBuilder({ page }).analyze();
    const serious = violations
      .filter((item) => ['serious', 'critical'].includes(item.impact))
      .map((item) => item.id);
    expect(serious, String(width)).toEqual([]);
  }
});
