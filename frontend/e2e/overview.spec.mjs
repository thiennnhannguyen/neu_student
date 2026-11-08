/** CR-05: Tổng quan của thiennhan, thẻ "Số môn chưa đạt" = số dòng trang đích ở S1–S5. */
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { seed } from './env.mjs';
import { login } from './helpers.mjs';

const EXPECTED = { S1: 0, S2: 1, S3: 2, S4: 1, S5: 1 };

test.beforeEach(() => seed());

function failedCard(page) {
  return page.getByRole('link', { name: 'Số môn chưa đạt' }).locator('xpath=ancestor::article');
}

async function seriousViolations(page) {
  await page.waitForLoadState('networkidle');
  const { violations } = await new AxeBuilder({ page }).analyze();
  return violations
    .filter((item) => ['serious', 'critical'].includes(item.impact))
    .map((item) => item.id);
}

test('S1–S5: số trên thẻ bằng số dòng trang đích, tên môn khớp API', async ({ page }) => {
  await login(page, 'thiennhan');
  const rows = {};
  for (const [semester, count] of Object.entries(EXPECTED)) {
    await page.goto(`/?semester=${semester}`);
    const card = failedCard(page);
    await expect(card.locator('.metric-card__value')).toHaveText(String(count));
    await page.getByRole('link', { name: 'Số môn chưa đạt' }).click();
    await expect(page).toHaveURL(
      new RegExp(`semester=${semester}.*view=failed|view=failed.*semester=${semester}`),
    );
    const heading = page.getByRole('heading', {
      name: /^Môn chưa đạt tính đến HK\d \d{4}-\d{4}: \d+ môn$/,
    });
    await expect(heading).toContainText(`: ${count} môn`);
    const body = page.locator('.ui-table tbody tr');
    await expect(body).toHaveCount(count);
    rows[semester] = await page
      .locator('.ui-table tbody tr .cell-stack > span:first-child')
      .allInnerTexts();
    const api = await page.request.get(`/api/m11/grades?semester_id=${semester}&view=failed_as_of`);
    const names = (await api.json()).items.map((item) => item.name);
    expect(rows[semester].sort()).toEqual(names.sort());
  }
  test.info().annotations.push({ type: 'S1–S5', description: JSON.stringify(rows) });
});

test('tải lại, Back/Forward giữ phạm vi "tính đến"', async ({ page }) => {
  await login(page, 'thiennhan');
  await page.goto('/?semester=S3');
  await page.getByRole('link', { name: 'Số môn chưa đạt' }).click();
  const heading = page.getByRole('heading', { name: 'Môn chưa đạt tính đến HK1 2025-2026: 2 môn' });
  await expect(heading).toBeVisible();
  await page.reload();
  await expect(heading).toBeVisible();
  await page.getByRole('button', { name: 'Xem bảng điểm kỳ này' }).click();
  await expect(page).not.toHaveURL(/view=failed/);
  await page.goBack();
  await expect(heading).toBeVisible();
  await page.goForward();
  await expect(page).not.toHaveURL(/view=failed/);
  await page.goBack();
  await page.goBack();
  await expect(page).toHaveURL(/\/\?semester=S3$/);
  await expect(failedCard(page).locator('.metric-card__value')).toHaveText('2');
});

test('đổi kỳ nhanh liên tiếp: cuối cùng hiện đúng số của kỳ được chọn', async ({ page }) => {
  await login(page, 'thiennhan');
  await page.goto('/');
  const select = page.locator('#overview-semester');
  await expect(failedCard(page).locator('.metric-card__value')).toHaveText('1');
  await select.selectOption('S3');
  await select.selectOption('S1');
  await select.selectOption('S3');
  await expect(failedCard(page).locator('.metric-card__value')).toHaveText('2');
  await expect(page.getByText('Tính đến HK1 2025-2026').first()).toBeVisible();
});

test('375px: mở tấm chọn kỳ bằng bàn phím, Esc đóng và trả focus về chip', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await login(page, 'thiennhan');
  await page.goto('/');
  const chip = page.getByRole('button', { name: /^Đang xem: HK1 2026-2027/ });
  await chip.focus();
  await page.keyboard.press('Enter');
  const sheet = page.getByRole('dialog', { name: 'Chọn phạm vi xem' });
  await expect(sheet).toBeVisible();
  await page.keyboard.press('Tab');
  const focused = await page.evaluate(
    () => document.activeElement?.closest('[role="dialog"]') !== null,
  );
  expect(focused).toBe(true);
  await page.keyboard.press('Escape');
  await expect(sheet).toBeHidden();
  await expect(chip).toBeFocused();
  const outline = await chip.evaluate(
    (node) => node.ownerDocument.defaultView.getComputedStyle(node).outlineStyle,
  );
  expect(outline).not.toBe('none');
});

test('axe: Tổng quan, trang đích, Kết quả, Phân tích ở 1440 và 375', async ({ page }) => {
  await login(page, 'thiennhan');
  for (const width of [1440, 375]) {
    await page.setViewportSize({ width, height: width === 375 ? 812 : 1000 });
    for (const url of [
      '/?semester=S3',
      '/m11/ket-qua?semester=S3&view=failed',
      '/m11/ket-qua',
      '/m11/phan-tich',
    ]) {
      await page.goto(url);
      expect(await seriousViolations(page), `${url} ${width}`).toEqual([]);
    }
  }
});
