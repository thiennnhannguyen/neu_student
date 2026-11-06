import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  HEADER_STRIP,
  ILLUSTRATION,
  LEFT_STRIP,
  MOBILE_BAND,
  RIGHT_STRIP,
  SIDEBAR_BAND,
  TABLET_BAND,
  WELCOME_MOSAIC,
} from './mosaicLayouts';
import MotifMosaic, { MOSAIC_FADE_MS, MOSAIC_MAX_DELAY_MS } from './MotifMosaic';
import { MOTIFS } from './motifs';
import { tokenColor } from './motifs/MotifFrame';

const EXPECTED_MOTIFS = [
  'CircleDiamond',
  'DiagonalSplit',
  'QuarterCircle',
  'HalfCircle',
  'DotTriangle',
  'Stripes',
  'Zigzag',
  'Arcs',
  'Petals',
  'Gear',
  'RisingBars',
  'Building',
  'DiagonalN',
  'CircuitCircle',
  'Books',
  'LetterK',
  'Globe',
  'TwoPeople',
  'FourPointStar',
];
const LAYOUTS = {
  LEFT_STRIP,
  RIGHT_STRIP,
  TABLET_BAND,
  MOBILE_BAND,
  SIDEBAR_BAND,
  HEADER_STRIP,
  WELCOME_MOSAIC,
  ILLUSTRATION,
};

function adjacentPairs({ rows, cols, layout }) {
  const pairs = [];
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const cell = layout[row * cols + col];
      if (col + 1 < cols) {
        pairs.push([cell, layout[row * cols + col + 1]]);
      }
      if (row + 1 < rows) {
        pairs.push([cell, layout[(row + 1) * cols + col]]);
      }
    }
  }
  return pairs;
}

describe('thư viện họa tiết', () => {
  it('có đúng 19 họa tiết (14 của CR-01, 5 của Q72)', () => {
    expect(Object.keys(MOTIFS).sort()).toEqual([...EXPECTED_MOTIFS].sort());
  });

  it.each(EXPECTED_MOTIFS)('%s: SVG 100 x 100, dùng token, không có chữ', (name) => {
    const Motif = MOTIFS[name];

    const { container } = render(<Motif bg="tint" fg="primary" />);

    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('viewBox', '0 0 100 100');
    expect(svg).toHaveAttribute('aria-hidden', 'true');
    expect(svg).toHaveAttribute('focusable', 'false');
    expect(svg.querySelector('text')).toBeNull();
    expect(svg.querySelector('filter')).toBeNull();
    expect(svg.querySelector('rect')).toHaveAttribute('fill', 'var(--neu-tint)');
    expect(svg.innerHTML).toContain('var(--neu-primary)');
    expect(svg.innerHTML).not.toMatch(/#[0-9a-f]{3,8}\b/i);
    expect(svg.textContent).toBe('');
  });

  it('bánh răng có đúng 8 răng', () => {
    const { container } = render(<MOTIFS.Gear bg="tint" fg="primary" />);

    const points = container.querySelector('polygon').getAttribute('points').split(' ');

    expect(points).toHaveLength(8 * 4);
  });

  it('từ chối token màu không tồn tại', () => {
    expect(() => tokenColor('do')).toThrow();
    expect(tokenColor('primary-dark')).toBe('var(--neu-primary-dark)');
  });
});

describe('bố cục mosaic', () => {
  it.each(Object.keys(LAYOUTS))('%s: đủ ô, chỉ dùng họa tiết có thật', (name) => {
    const { rows, cols, layout } = LAYOUTS[name];

    expect(layout).toHaveLength(rows * cols);
    for (const [motif, bg, fg] of layout) {
      expect(MOTIFS[motif]).toBeDefined();
      expect(tokenColor(bg)).toBeTruthy();
      expect(tokenColor(fg)).toBeTruthy();
      expect(bg).not.toBe(fg);
    }
  });

  it.each(Object.keys(LAYOUTS))(
    '%s: 2 ô cạnh nhau không trùng họa tiết, không trùng cặp màu',
    (name) => {
      const pairs = adjacentPairs(LAYOUTS[name]);

      expect(pairs.length).toBeGreaterThan(0);
      for (const [first, second] of pairs) {
        expect(first[0]).not.toBe(second[0]);
        expect(`${first[1]}/${first[2]}`).not.toBe(`${second[1]}/${second[2]}`);
      }
    },
  );

  it('bố cục giống hệt nhau giữa các lần render', () => {
    const first = render(<MotifMosaic {...MOBILE_BAND} />).container.innerHTML;
    const second = render(<MotifMosaic {...MOBILE_BAND} />).container.innerHTML;

    expect(first).toBe(second);
  });

  it('từ chối số ô không khớp rows x cols', () => {
    expect(() => render(<MotifMosaic rows={2} cols={2} layout={MOBILE_BAND.layout} />)).toThrow();
  });
});

describe('MotifMosaic', () => {
  it('aria-hidden, không có phần tử nhận focus', () => {
    const { container } = render(<MotifMosaic {...MOBILE_BAND} />);

    const mosaic = container.firstChild;
    expect(mosaic).toHaveAttribute('aria-hidden', 'true');
    expect(mosaic.querySelector('a, button, input, [tabindex]')).toBeNull();
    for (const svg of mosaic.querySelectorAll('svg')) {
      expect(svg).toHaveAttribute('focusable', 'false');
    }
  });

  it('tổng thời gian hiện dần không quá 600ms', () => {
    const { container } = render(<MotifMosaic {...LEFT_STRIP} />);

    const finishTimes = [...container.querySelectorAll('.motif-mosaic__cell')].map(
      (cell) =>
        parseInt(cell.style.animationDelay, 10) + parseInt(cell.style.animationDuration, 10),
    );

    expect(MOSAIC_MAX_DELAY_MS + MOSAIC_FADE_MS).toBeLessThanOrEqual(600);
    expect(Math.max(...finishTimes)).toBeLessThanOrEqual(600);
    expect(Math.max(...finishTimes)).toBeGreaterThan(MOSAIC_FADE_MS);
  });
});
