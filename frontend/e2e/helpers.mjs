import { expect } from '@playwright/test';

export const PASSWORD = 'Demo@12345';

export async function login(page, username) {
  // Rời trang trước: request đang chờ trả về sẽ ký lại cookie phiên ngay sau khi xóa.
  await page.goto('about:blank');
  await page.context().clearCookies();
  await page.goto('/login');
  await page.getByLabel('Tên đăng nhập').fill(username);
  await page.locator('#login-password').fill(PASSWORD);
  await page.getByRole('button', { name: 'Đăng nhập' }).click();
  await expect(page).not.toHaveURL(/\/login/);
}

export async function skillNumerator(page, careerId) {
  const response = await page.request.get('/api/m12/gallery');
  const { items } = await response.json();
  return items.find((item) => item.career.id === careerId).skill_progress.numerator;
}
