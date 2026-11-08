import { expect } from '@playwright/test';

export const PASSWORD = 'Demo@12345';

const ANSWERS = {
  attendance: 'present',
  self_study: '1_2h',
  understanding: 4,
  unclear_note: null,
  assignment: 'done',
  confidence: 4,
  obstacle: 'none',
  next_plan: 'keep_going',
};

/**
 * D-312: nộp sẵn các báo cáo tuần đang mở qua API để màn hình báo cáo toàn trang không che kịch bản
 * không liên quan. Vai trò khác sinh viên nhận 403 nên bỏ qua. Trả số báo cáo đã nộp.
 */
export async function submitOpenWeeklyReports(page) {
  const response = await page.request.get('/api/weekly-reports/open');
  if (!response.ok()) {
    return 0;
  }
  const { items } = await response.json();
  for (const item of items) {
    const submitted = await page.request.post(
      `/api/weekly-reports/${item.course.id}/${item.week.week_no}/submit`,
      { data: ANSWERS, headers: { 'X-Requested-With': 'fetch' } },
    );
    expect(submitted.ok()).toBeTruthy();
  }
  return items.length;
}

/**
 * Đăng nhập. Mặc định nộp sẵn báo cáo tuần đang mở (D-312) rồi tải lại trang; kịch bản báo cáo
 * tuần truyền { keepWeeklyReports: true } để giữ màn hình báo cáo.
 */
export async function login(page, username, { keepWeeklyReports = false } = {}) {
  // Rời trang trước: request đang chờ trả về sẽ ký lại cookie phiên ngay sau khi xóa.
  await page.goto('about:blank');
  await page.context().clearCookies();
  await page.goto('/login');
  await page.getByLabel('Tên đăng nhập').fill(username);
  await page.locator('#login-password').fill(PASSWORD);
  await page.getByRole('button', { name: 'Đăng nhập' }).click();
  await expect(page).not.toHaveURL(/\/login/);
  if (!keepWeeklyReports && (await submitOpenWeeklyReports(page)) > 0) {
    await page.reload();
  }
}

export async function skillNumerator(page, careerId) {
  const response = await page.request.get('/api/m12/gallery');
  const { items } = await response.json();
  return items.find((item) => item.career.id === careerId).skill_progress.numerator;
}
