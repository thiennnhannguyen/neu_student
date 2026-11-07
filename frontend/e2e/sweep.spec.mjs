/** Rà mọi trang ở 375, 768, 1280: không tràn ngang, 1 tiêu đề chính, họa tiết đúng vị trí. */
import { expect, test } from '@playwright/test';
import { seed } from './env.mjs';
import { login } from './helpers.mjs';

const WIDTHS = [375, 768, 1280];
const PAGES = [
  [null, '/login'],
  ['demo05', '/'],
  ['demo05', '/ho-so'],
  ['demo05', '/m11/ket-qua'],
  ['demo05', '/m11/phan-tich'],
  ['demo05', '/m11/canh-bao'],
  ['demo05', '/m11/canh-bao/ke-hoach'],
  ['demo05', '/m12/dinh-huong'],
  ['demo05', '/m12/dinh-huong/nghe/ai-engineer'],
  ['demo05', '/m12/ke-hoach'],
  ['demo05', '/m12/ke-hoach/khac-biet'],
  ['demo05', '/m12/hoc-lieu'],
  ['demo05', '/m12/nhac-nho'],
  ['demo05', '/m12/yeu-cau-ho-tro'],
  ['demo05', '/khong-co-trang-nay'],
  ['gv2', '/'],
  ['gv2', '/m12/duyet-minh-chung'],
  ['gv2', '/m11/ket-qua?student_id=DEMO05'],
  ['gv2', '/m12/yeu-cau-ho-tro'],
  ['ht1', '/'],
  ['ht1', '/m12/yeu-cau-ho-tro'],
  ['admin', '/'],
  ['admin', '/quan-tri/nhat-ky'],
  ['admin', '/m12/yeu-cau-ho-tro'],
];
// Vị trí được phép theo AGENTS.md và D-218. Trang đăng nhập có bố cục riêng.
const ALLOWED_MOTIF_PARENTS = [
  '.sidebar',
  '.page-header',
  '.welcome-card',
  '.empty-block',
  '.error-block',
  '.not-found',
  '.login-brand',
  '.login-page',
  '.career-primary',
  '.career-hero',
];

test.beforeAll(() => seed());

for (const width of WIDTHS) {
  test.describe(`${width}px`, () => {
    test.use({ viewport: { width, height: 900 } });

    for (const [username, path] of PAGES) {
      test(`${username ?? 'chưa đăng nhập'} ${path}`, async ({ page }) => {
        if (username) {
          await login(page, username);
        }
        await page.goto(path);
        await page.waitForLoadState('networkidle');

        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
        );
        expect(overflow).toBe(0);
        await expect(page.locator('h1')).toHaveCount(1);
        const misplaced = await page.evaluate(
          (allowed) =>
            [...document.querySelectorAll('.motif-mosaic')]
              .filter((motif) => !allowed.some((selector) => motif.closest(selector)))
              .map((motif) => motif.className.baseVal ?? motif.className),
          ALLOWED_MOTIF_PARENTS,
        );
        expect(misplaced).toEqual([]);
      });
    }
  });
}

test.describe('nhãn thẻ chỉ số ở 375px', () => {
  test.use({ viewport: { width: 375, height: 812 } });

  test('mỗi nhãn nằm trên 1 dòng, không tràn thẻ', async ({ page }) => {
    await login(page, 'demo05');
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const labels = page.locator('.metric-grid .metric-card__link');
    await expect(labels).toHaveCount(4);
    const measured = await labels.evaluateAll((items) =>
      items.map((item) => {
        const label = item.getBoundingClientRect();
        const card = item.closest('.metric-card').getBoundingClientRect();
        const icon = item.closest('.metric-card__head').querySelector('svg');
        const glyph = icon.getBoundingClientRect();
        return {
          text: item.textContent,
          lines: item.getClientRects().length,
          clearOfIcon: label.right <= glyph.left,
          iconInCard: glyph.right <= card.right,
        };
      }),
    );
    for (const label of measured) {
      expect(label).toEqual({ text: label.text, lines: 1, clearOfIcon: true, iconInCard: true });
    }
  });
});
