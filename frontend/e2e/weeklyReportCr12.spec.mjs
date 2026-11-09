/** CR-12 (D-312): báo cáo tuần toàn trang ở ngày demo 26/10/2026, qua API thật. */
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { seed } from './env.mjs';
import { login } from './helpers.mjs';

test.beforeEach(() => seed());

async function seriousViolations(page) {
  const { violations } = await new AxeBuilder({ page }).analyze();
  return violations
    .filter((item) => ['serious', 'critical'].includes(item.impact))
    .map((item) => item.id);
}

async function answerAll(dialog) {
  for (const [group, option] of [
    ['1. Đi học tuần này', 'Có mặt'],
    ['2. Thời gian tự học', '1–2 giờ'],
    ['3. Mức hiểu bài tuần này', '3'],
    ['5. Bài tập tuần này', 'Không có bài'],
    ['6. Mức tự tin nếu thi ngay bây giờ', '3'],
    ['7. Cản trở nhiều nhất', 'Lịch học dày'],
    ['8. Tuần tới định làm gì', 'Ôn lại bài'],
  ]) {
    await dialog
      .getByRole('group', { name: new RegExp(group) })
      .getByRole('radio', { name: option, exact: true })
      .check();
  }
}

// D-314: cột "Báo cáo tuần" chuyển vào mục "Báo cáo tuần" của trang chi tiết môn.
function weeklySection(page) {
  return page.getByRole('region', { name: 'Báo cáo tuần', exact: true });
}

for (const width of [1440, 375]) {
  test(`${width}px: thiennhan thấy "Môn 1/2", hạn gần nhất trước, axe không lỗi`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await login(page, 'thiennhan', { keepWeeklyReports: true });
    const dialog = page.getByRole('dialog', { name: /CNTT1180/ });
    await expect(dialog).toBeVisible();
    await expect(dialog).toContainText('Báo cáo tuần · Môn 1/2');
    await expect(dialog).toContainText('Tuần 7 (19/10/2026–25/10/2026)');
    await expect(dialog).toContainText('Hạn nộp hết ngày 26/10/2026');
    await expect(dialog).toContainText('cố vấn học tập được phân công có thể xem');
    await expect(page.getByRole('heading', { name: /CNTT1180/ })).toBeFocused();
    expect(await seriousViolations(page)).toEqual([]);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      ),
    ).toBe(0);
  });
}

test('Làm sau, nộp môn 2/2, tải lại thì hiện lại không còn Làm sau, Esc không đóng', async ({
  page,
}) => {
  await login(page, 'thiennhan', { keepWeeklyReports: true });
  await page
    .getByRole('dialog', { name: /CNTT1180/ })
    .getByRole('button', { name: 'Làm sau' })
    .click();
  const second = page.getByRole('dialog', { name: /CNTT1117/ });
  await expect(second).toContainText('Môn 2/2');
  await answerAll(second);
  await second.getByRole('button', { name: 'Nộp báo cáo' }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);

  // Chuyển trang trong lần dùng này: CNTT1180 đã "Làm sau" nên không hiện.
  await page
    .getByRole('navigation', { name: 'Menu chính' })
    .getByRole('link', {
      name: 'Phân tích & Cảnh báo',
    })
    .click();
  // Bấm dòng của môn trong bảng để mở trang chi tiết.
  await page.getByRole('link', { name: /CNTT1117\s*: điểm dự kiến/ }).click();
  await expect(weeklySection(page)).toContainText('Đã nộp 8/8 · gần nhất tuần 8 (26/10/2026)');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  // Quay lại bảng bằng liên kết trong trang (không tải lại, nên CNTT1180 vẫn đang "Làm sau").
  await page.locator('.back-link').click();
  await page.getByRole('link', { name: /CNTT1180\s*: điểm dự kiến/ }).click();
  await expect(weeklySection(page)).toContainText('Đã nộp 6/6 · gần nhất tuần 6');
  await expect(weeklySection(page)).toContainText('1 đang mở');
  await expect(page.getByRole('dialog')).toHaveCount(0);

  // Tải lại trang: hiện lại CNTT1180, không còn "Làm sau", Esc không đóng.
  await page.reload();
  const again = page.getByRole('dialog', { name: /CNTT1180/ });
  await expect(again).toContainText('Môn 1/1');
  await expect(again.getByRole('button', { name: 'Làm sau' })).toHaveCount(0);
  await page.keyboard.press('Escape');
  await expect(again).toBeVisible();
});

test('không chặn Yêu cầu hỗ trợ', async ({ page }) => {
  await login(page, 'thiennhan', { keepWeeklyReports: true });
  await page.getByRole('dialog').getByRole('button', { name: 'Yêu cầu hỗ trợ' }).click();
  await expect(page).toHaveURL(/\/m12\/yeu-cau-ho-tro$/);
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
});

test('cố vấn xem lại báo cáo tuần của sinh viên được phân công, chỉ đọc', async ({ page }) => {
  await login(page, 'gv2');
  await page.goto('/m11/phan-tich/mon/CNTT1140?student=NEU-KHMT-001');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  const row = weeklySection(page);
  await expect(row).toContainText('Đã nộp 5/7 · gần nhất tuần 6 (14/10/2026)');
  await row.getByRole('button', { name: 'Xem báo cáo tuần môn CNTT1140' }).click();
  const panel = page.getByRole('dialog', { name: /Báo cáo tuần CNTT1140/ });
  await expect(panel).toContainText('Không nộp');
  await expect(panel).toContainText('Chưa hiểu mạng nơ-ron nhiều lớp.');
  await expect(panel.getByRole('radio')).toHaveCount(0);
  expect(await seriousViolations(page)).toEqual([]);
});
