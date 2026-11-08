import { expect, test } from '@playwright/test';
import { seed } from './env.mjs';
import { login, skillNumerator } from './helpers.mjs';

const AI_PAGE = '/m12/dinh-huong/nghe/ai-engineer';
const AI_ID = 'career-k68-ai';

test.beforeEach(() => seed());

test('1. đăng nhập rồi vào Tổng quan M11', async ({ page }) => {
  await login(page, 'demo05');

  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole('link', { name: 'GPA tích lũy' })).toBeVisible();
  await expect(page.getByText('Mức cảnh báo chung')).toBeVisible();
});

async function openCoursePanelByKeyboard(page) {
  await login(page, 'demo05');
  await page.goto('/m12/dinh-huong');
  await page.locator(`a[href*="/nghe/ai-engineer"]`).first().click();
  await expect(page).toHaveURL(/\/nghe\/ai-engineer/);

  const stage = page.getByRole('tree').getByRole('treeitem').first();
  await stage.focus();
  if ((await stage.getAttribute('aria-expanded')) === 'false') {
    await page.keyboard.press('ArrowRight');
  }
  await page.keyboard.press('ArrowRight');
  const course = page.getByRole('tree').getByRole('treeitem', { level: 2 }).first();
  await expect(course).toBeFocused();
  await page.keyboard.press('Enter');
  return course;
}

test('2. lưới nghề, trang AI Engineer, panel môn bằng bàn phím, Esc trả focus', async ({
  page,
}) => {
  const course = await openCoursePanelByKeyboard(page);

  const panel = page.locator('.side-panel');
  await expect(panel).toBeVisible();
  await expect(panel.getByRole('button', { name: 'Đóng' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(panel).toBeHidden();
  await expect(course).toBeFocused();
});

test.describe('ở 375px', () => {
  test.use({ viewport: { width: 375, height: 812 } });

  test('2. lưới nghề, trang AI Engineer, panel môn bằng bàn phím, Esc trả focus', async ({
    page,
  }) => {
    const course = await openCoursePanelByKeyboard(page);

    const panel = page.getByRole('dialog');
    await expect(panel).toBeVisible();
    await expect(panel.getByRole('button', { name: 'Đóng' })).toBeFocused();
    await page.keyboard.press('Escape');
    await expect(panel).toBeHidden();
    await expect(course).toBeFocused();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBe(0);
  });
});

test('3. nộp minh chứng, cố vấn duyệt, sinh viên thấy % đổi và thông báo', async ({ page }) => {
  await login(page, 'demo05');
  const before = await skillNumerator(page, AI_ID);
  await page.goto(AI_PAGE);
  await page.getByRole('tab', { name: 'Kỹ năng & dự án' }).click();
  await page.getByRole('button', { name: 'Nộp minh chứng' }).first().click();
  const form = page.locator('.side-panel');
  const skill = await form.getByRole('heading').first().textContent();
  await form.getByLabel('Mô tả').fill('Kho mã và báo cáo của nhóm');
  await form.getByRole('button', { name: 'Nộp minh chứng' }).click();
  await expect(form.getByRole('img', { name: 'Chờ duyệt' }).first()).toBeVisible();

  await login(page, 'gv2');
  await page.goto('/m12/duyet-minh-chung');
  const row = page.getByRole('row', { name: new RegExp(skill) });
  await row.getByRole('button', { name: 'Xem' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Duyệt' }).click();
  await expect(page.getByRole('dialog')).toBeHidden();

  await login(page, 'demo05');
  expect(await skillNumerator(page, AI_ID)).toBe(before + 1);
  await page.goto(AI_PAGE);
  await page.getByRole('button', { name: /Thông báo, \d+ chưa đọc/ }).click();
  await expect(page.getByLabel('Danh sách thông báo')).toContainText(
    `Minh chứng ${skill} đã được duyệt`,
  );
});

test('4. tạo lộ trình, đổi nghề chính, xem khác biệt, áp dụng', async ({ page }) => {
  await login(page, 'demo05');
  await page.goto('/m12/ke-hoach');
  await page.getByRole('button', { name: 'Tạo lộ trình' }).click();
  await expect(page.getByRole('group', { name: 'Lộ trình theo học kỳ' })).toBeVisible();

  await page.goto('/m12/dinh-huong/nghe/data-analyst');
  await page.getByRole('button', { name: 'Đặt làm mục tiêu chính' }).click();
  await page.getByRole('alertdialog').getByRole('button', { name: 'Xác nhận' }).click();
  await expect(page.getByRole('alertdialog')).toBeHidden();

  await page.goto('/m12/ke-hoach');
  await page.getByRole('link', { name: 'Xem khác biệt' }).click();
  await expect(page).toHaveURL(/\/m12\/ke-hoach\/khac-biet/);
  await expect(page.getByRole('heading', { name: 'Bản đề xuất' }).first()).toBeVisible();
  await page.getByRole('button', { name: /Áp dụng/ }).click();
  await expect(page.getByText(/Đã áp dụng/)).toBeVisible();
  await page.goto('/m12/ke-hoach');
  await expect(page.getByRole('link', { name: 'Xem khác biệt' })).toHaveCount(0);
});

test('5. demo01 tạo ticket, ht1 chuyển cần bổ sung, demo01 trả lời', async ({ page }) => {
  await login(page, 'demo01');
  await page.goto('/m12/yeu-cau-ho-tro');
  await page.getByRole('button', { name: 'Tạo yêu cầu' }).click();
  await page.getByLabel('Tiêu đề').fill('Xin xác nhận đăng ký học phần');
  await page.getByLabel('Nhóm vấn đề').selectOption({ label: 'Học vụ' });
  await page.getByLabel('Mô tả').fill('Em cần xác nhận trước hạn.');
  await page.getByRole('button', { name: 'Gửi yêu cầu' }).click();
  await expect(page).toHaveURL(/\/m12\/yeu-cau-ho-tro\/.+/);
  const ticketUrl = page.url();

  await login(page, 'ht1');
  await page.goto(ticketUrl);
  await page.getByRole('button', { name: 'Chuyển sang Đang xử lý' }).click();
  await page.getByRole('button', { name: 'Chuyển sang Cần bổ sung' }).click();
  await expect(page.getByRole('button', { name: 'Chuyển sang Hoàn thành' })).toBeVisible();

  await login(page, 'demo01');
  await page.goto(ticketUrl);
  await page.getByLabel('Trả lời').fill('Em bổ sung mã học phần.');
  await page.getByRole('button', { name: 'Gửi', exact: true }).click();
  await expect(page.getByText('Em bổ sung mã học phần.')).toBeVisible();
  await expect(page.getByLabel('Trả lời')).toBeHidden();
});
