/** thiennhan làm bài mô-đun 3, đạt, có chứng chỉ, mở trang xác thực khi chưa đăng nhập. */
import { readFileSync } from 'node:fs';
import { URL } from 'node:url';
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { seed } from './env.mjs';
import { login } from './helpers.mjs';

const FRAMEWORK_PAGE = '/m12/dinh-huong/nghe/backend-developer?tab=framework';
const fixture = JSON.parse(
  readFileSync(
    new URL('../../backend/app/seed/fixtures_demo_k68/framework.json', import.meta.url),
    'utf8',
  ),
);

function rightOptions(prompt) {
  const plain = (text) => text.replaceAll('`', '');
  const question = fixture.quiz_questions.find((row) => plain(row.prompt) === prompt);
  return fixture.quiz_options
    .filter((row) => row.question_id === question.id && row.is_correct)
    .map((row) => plain(row.text));
}

/** Khớp nguyên nhãn: đáp án này có thể là chuỗi con của đáp án khác, bấm nhầm sẽ bỏ chọn. */
function optionLabel(group, text) {
  const escaped = text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return group.locator('label').filter({ hasText: new RegExp(`^\\s*${escaped}\\s*$`) });
}

async function answerAll(page, correct = true) {
  const groups = page.locator('.quiz-question fieldset');
  await expect(groups).toHaveCount(10);
  for (let index = 0; index < 10; index += 1) {
    const group = groups.nth(index);
    const legend = (await group.locator('legend').innerText()).replace(/^Câu \d+\. /, '');
    const right = rightOptions(legend);
    if (correct) {
      for (const text of right) {
        await optionLabel(group, text).click();
      }
      await expect(group.locator('input:checked')).toHaveCount(right.length);
    } else {
      const wrong = group.locator('label').filter({ hasNotText: right[0] }).first();
      await wrong.click();
    }
  }
}

async function submit(page) {
  await page.getByRole('button', { name: 'Nộp bài' }).click();
  await page.getByRole('alertdialog').getByRole('button', { name: 'Nộp bài' }).click();
}

function moduleCard(page, order) {
  return page.locator('.module-card', { hasText: `Mô-đun ${order}` }).first();
}

test.beforeEach(() => seed());

test('thiennhan đạt mô-đun 3, có chứng chỉ, xác thực được khi chưa đăng nhập', async ({
  page,
  browser,
}) => {
  await login(page, 'thiennhan');
  await page.goto(FRAMEWORK_PAGE);
  await moduleCard(page, 3).getByRole('button', { name: 'Làm bài kiểm tra' }).click();

  await expect(page).toHaveURL(/\/m12\/lam-bai\//);
  await expect(page.getByText(/Câu hỏi do nhóm biên soạn/)).toBeVisible();
  await answerAll(page);
  await submit(page);

  await expect(page.getByText('10/10 câu đúng (100%)')).toBeVisible();
  await page.getByRole('link', { name: 'Xem chứng chỉ' }).click();

  const certificate = page.locator('.certificate');
  await expect(certificate).toContainText('Nguyễn Thiện Nhân');
  await expect(certificate).toContainText('Cơ sở dữ liệu và SQL');
  await expect(certificate).toContainText(
    'không phải chứng chỉ của Trường Đại học Kinh tế Quốc dân',
  );
  await expect(certificate.getByRole('img', { name: 'Mã QR tới trang xác thực' })).toBeVisible();
  const url = await certificate.locator('.certificate__url').innerText();

  await page.goto(FRAMEWORK_PAGE);
  await expect(moduleCard(page, 3)).toContainText('Đã đạt');
  await expect(moduleCard(page, 3).getByRole('link', { name: 'Ôn tập' })).toBeVisible();
  await expect(moduleCard(page, 3).getByRole('button', { name: 'Làm bài kiểm tra' })).toHaveCount(
    0,
  );

  const stranger = await browser.newContext();
  const open = await stranger.newPage();
  await open.goto(url);
  await expect(open.getByRole('heading', { level: 1, name: 'Xác thực chứng chỉ' })).toBeVisible();
  await expect(open.getByText('Nguyễn Thiện Nhân')).toBeVisible();
  await expect(open.getByText('Còn hiệu lực')).toBeVisible();
  await expect(open.getByText('Dữ liệu mẫu')).toHaveCount(0);
  await expect(open.getByText('không phải hệ thống chính thức').first()).toBeVisible();
  await open.goto(`${new URL(url).origin}/xac-thuc/ma-sai`);
  await expect(open.getByText('Không tìm thấy chứng chỉ với mã này')).toBeVisible();
  await stranger.close();
});

test('trượt thì có giờ làm lại, chưa có chứng chỉ', async ({ page }) => {
  await login(page, 'thiennhan');
  await page.goto(FRAMEWORK_PAGE);
  await moduleCard(page, 3).getByRole('button', { name: 'Làm bài kiểm tra' }).click();
  await answerAll(page, false);
  await submit(page);

  await expect(page.getByText(/Chưa đạt, cần từ 80%/)).toBeVisible();
  await expect(page.getByText(/Làm lại từ/)).toBeVisible();
  await expect(page.getByRole('link', { name: 'Xem chứng chỉ' })).toHaveCount(0);

  await page.goto(FRAMEWORK_PAGE);
  await expect(
    moduleCard(page, 3).getByRole('button', { name: 'Làm bài kiểm tra' }),
  ).toBeDisabled();
});

test.describe('axe các trang mới', () => {
  async function serious(page) {
    await page.waitForLoadState('networkidle');
    const { violations } = await new AxeBuilder({ page }).analyze();
    return violations
      .filter((item) => ['serious', 'critical'].includes(item.impact))
      .map((item) => item.id);
  }

  test('khung năng lực, bài kiểm tra, chứng chỉ, xác thực: 0 serious/critical', async ({
    page,
  }) => {
    await login(page, 'thiennhan');
    await page.goto(FRAMEWORK_PAGE);
    await page.locator('.module-card summary').first().click();
    expect(await serious(page)).toEqual([]);

    await page.goto('/m12/chung-chi');
    expect(await serious(page)).toEqual([]);

    await page.getByRole('link', { name: 'Xem chứng chỉ' }).first().click();
    await expect(page.locator('.certificate')).toBeVisible();
    expect(await serious(page)).toEqual([]);
    const url = await page.locator('.certificate__url').innerText();
    await page.goto(url);
    await expect(page.getByText('Còn hiệu lực')).toBeVisible();
    expect(await serious(page)).toEqual([]);

    await page.goto(FRAMEWORK_PAGE);
    await moduleCard(page, 3).getByRole('button', { name: 'Làm bài kiểm tra' }).click();
    await expect(page.locator('.quiz-question').first()).toBeVisible();
    expect(await serious(page)).toEqual([]);
    await answerAll(page);
    await submit(page);
    await expect(page.getByText('10/10 câu đúng (100%)')).toBeVisible();
    expect(await serious(page)).toEqual([]);
  });
});
