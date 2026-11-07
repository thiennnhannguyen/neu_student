import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import process from 'node:process';
import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import CareerIllustration, { ILLUSTRATIONS } from './CareerIllustration';

const TOKENS = readFileSync(join(process.cwd(), 'src/styles/tokens.css'), 'utf8');

function luminance(hex) {
  const channels = [1, 3, 5].map((start) => parseInt(hex.slice(start, start + 2), 16) / 255);
  const [r, g, b] = channels.map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

describe('minh họa nghề', () => {
  it('có đủ 10 hình, mỗi hình 3–6 ô họa tiết và biểu tượng riêng', () => {
    const entries = Object.values(ILLUSTRATIONS);
    expect(entries).toHaveLength(10);
    expect(new Set(entries.map((entry) => entry.Icon)).size).toBe(10);
    entries.forEach((entry) => {
      expect(entry.cells.length).toBeGreaterThanOrEqual(3);
      expect(entry.cells.length).toBeLessThanOrEqual(6);
    });
  });

  it.each(Object.keys(ILLUSTRATIONS))('hình %s ẩn khỏi trợ năng, đúng viewBox 320×200', (key) => {
    const { container } = render(<CareerIllustration illustrationKey={key} />);
    const svg = container.firstChild;
    expect(svg).toHaveAttribute('aria-hidden', 'true');
    expect(svg).toHaveAttribute('viewBox', '0 0 320 200');
    expect(svg.textContent).toBe('');
  });

  it('nghề chưa có hình riêng vẫn có nền họa tiết', () => {
    const { container } = render(<CareerIllustration illustrationKey={null} />);
    expect(container.firstChild).toHaveAttribute('data-illustration', 'fallback');
  });

  it('6 sắc nhóm nghề đều đạt từ 4,5:1 trên nền trắng', () => {
    [1, 2, 3, 4, 5, 6].forEach((tone) => {
      const hex = TOKENS.match(new RegExp(`--career-tone-${tone}: (#[0-9a-f]{6})`))[1];
      expect(1.05 / (luminance(hex) + 0.05)).toBeGreaterThanOrEqual(4.5);
    });
  });
});
