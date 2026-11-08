/** CR-08 (D-306): Tổng quan theo ảnh mẫu trên bản build, số liệu của thiennhan đối chiếu API. */
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { seed } from './env.mjs';
import { login } from './helpers.mjs';

test.beforeEach(() => seed());

async function apiJson(page, path) {
  const response = await page.request.get(path);
  expect(response.ok(), path).toBe(true);
  return response.json();
}

function tableRows(page, name) {
  return page.getByRole('table', { name, includeHidden: true }).locator('tbody tr');
}

for (const semester of ['S5', 'S3']) {
  test(`thiennhan ${semester}: cột = kỳ có GPA, biểu đồ tròn cộng 100% và đủ tín chỉ CTĐT`, async ({
    page,
  }) => {
    await login(page, 'thiennhan');
    await page.goto(`/?semester=${semester}`);

    const trend = await apiJson(page, `/api/m11/gpa-trend?semester_id=${semester}`);
    const graded = trend.points.filter((point) => point.value !== null).map((point) => point.name);
    const barRows = tableRows(page, 'Điểm trung bình theo kỳ');
    await expect(barRows).toHaveCount(graded.length);
    expect(await barRows.locator('td:first-child').allTextContents()).toEqual(graded);
    expect(graded).not.toContain('HK1 2026-2027');
    // Mỗi kỳ có GPA là đúng một cột trên hình.
    await expect(page.locator('.gpa-bars .recharts-bar-rectangle')).toHaveCount(graded.length);

    const credits = await apiJson(page, `/api/m11/credits?semester_id=${semester}`);
    const total = credits.elective_groups.reduce(
      (sum, group) => sum + group.min_credits,
      credits.required.total_credits,
    );
    const pieRows = tableRows(page, 'Tín chỉ theo CTĐT');
    await expect(pieRows).toHaveCount(3);
    const cells = await pieRows.evaluateAll((rows) =>
      rows.map((row) => [...row.querySelectorAll('td')].map((cell) => cell.textContent)),
    );
    const sumCredits = cells.reduce((sum, row) => sum + parseInt(row[1], 10), 0);
    const sumTenths = cells.reduce((sum, row) => sum + parseInt(row[2].replace(/\D/g, ''), 10), 0);
    expect(sumCredits).toBe(total);
    expect(sumTenths).toBe(1000);
    expect(cells.map((row) => row[0])).toEqual([
      'Tín chỉ đã đạt',
      'Tín chỉ chưa đạt',
      'Tín chỉ chưa học',
    ]);

    test
      .info()
      .annotations.push({ type: semester, description: JSON.stringify({ graded, cells }) });
  });
}

for (const width of [1440, 375]) {
  test(`${width}px: nhãn biểu đồ từ 12px, không tràn ngang, bố cục đúng ảnh mẫu`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: width === 375 ? 812 : 1000 });
    await login(page, 'thiennhan');
    await page.goto('/');
    await expect(page.locator('.credit-pie__label').first()).toBeVisible();
    await expect(page.locator('.gpa-bars .recharts-xAxis-tick-labels text').first()).toBeVisible();

    const sizes = await page
      .locator('.credit-pie__label, .gpa-bars .recharts-cartesian-axis-tick-value, .chart-legend')
      .evaluateAll((nodes) =>
        nodes.map((node) =>
          parseFloat(node.ownerDocument.defaultView.getComputedStyle(node).fontSize),
        ),
      );
    expect(sizes.length).toBeGreaterThan(0);
    for (const size of sizes) {
      expect(size).toBeGreaterThanOrEqual(12);
    }

    // Nhãn biểu đồ tròn nằm trọn trong khung biểu đồ.
    const clipped = await page.locator('.credit-pie__label').evaluateAll(
      (nodes) =>
        nodes.filter((node) => {
          const box = node.getBoundingClientRect();
          const frame = node.closest('.overview-chart').getBoundingClientRect();
          return box.left < frame.left || box.right > frame.right;
        }).length,
    );
    expect(clipped).toBe(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      width,
    );

    const [cards, pie, bars] = await Promise.all(
      ['.overview-cards', '.overview-chart:has(.credit-pie)', '.overview-chart:has(.gpa-bars)'].map(
        (selector) => page.locator(selector).boundingBox(),
      ),
    );
    if (width === 375) {
      expect(cards.y + cards.height).toBeLessThanOrEqual(pie.y);
      expect(pie.y + pie.height).toBeLessThanOrEqual(bars.y);
    } else {
      expect(Math.abs(cards.y - pie.y)).toBeLessThan(2);
      expect(Math.abs(pie.y - bars.y)).toBeLessThan(2);
      expect(cards.x + cards.width).toBeLessThanOrEqual(pie.x);
      expect(pie.x + pie.width).toBeLessThanOrEqual(bars.x);
    }

    await page.waitForLoadState('networkidle');
    const { violations } = await new AxeBuilder({ page }).analyze();
    expect(
      violations.filter((item) => ['serious', 'critical'].includes(item.impact)).map((v) => v.id),
    ).toEqual([]);
  });
}

test('dải hồ sơ: mã SV mẫu, khóa · ngành; thẻ Số môn chưa đạt vẫn mở danh sách môn chưa đạt', async ({
  page,
}) => {
  await login(page, 'thiennhan');
  await page.goto('/?semester=S3');
  const band = page.getByRole('region', { name: 'Lời chào' });
  const profile = await apiJson(page, '/api/students/me');
  await expect(band).toContainText(`${profile.student_code} - ${profile.full_name}`);
  await expect(band).toContainText(`${profile.cohort} · ${profile.program.name}`);
  await expect(page.locator('#overview-semester')).toHaveValue('S3');
  await page.getByRole('link', { name: 'Số môn chưa đạt' }).click();
  await expect(page).toHaveURL(/\/m11\/ket-qua\?semester=S3&view=failed$/);
});
