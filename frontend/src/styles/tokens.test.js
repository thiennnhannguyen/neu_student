import { readdirSync, readFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import process from 'node:process';
import { describe, expect, it } from 'vitest';

// Đọc trực tiếp từ đĩa: trong Vitest, import CSS dạng ?raw trả về chuỗi rỗng.
const ROOT = process.cwd();
const SRC = join(ROOT, 'src');
const CODE_FILE = /\.(css|jsx?)$/;

function readSource(path) {
  return readFileSync(join(ROOT, path), 'utf8');
}

const SOURCES = Object.fromEntries(
  [
    'index.html',
    ...readdirSync(SRC, { recursive: true })
      .filter((name) => CODE_FILE.test(name))
      .map((name) => relative(ROOT, join(SRC, name))),
  ].map((path) => [path, readSource(path)]),
);
const tokensCss = SOURCES['src/styles/tokens.css'];
const globalCss = SOURCES['src/styles/global.css'];

const COLOR_PATTERNS = [
  /#[0-9a-f]{3,8}\b/gi,
  /\b(?:rgb|rgba|hsl|hsla)\(/gi,
  /(?:color|background|fill|stroke|border)[\w-]*\s*[:=]\s*["']?(?:white|black|red|blue|green)\b/gi,
];

function findLooseColors(source) {
  return COLOR_PATTERNS.flatMap((pattern) => source.match(pattern) ?? []);
}

function isChecked(path) {
  return !path.endsWith('/tokens.css') && !/\.test\.jsx?$/.test(path);
}

function token(name) {
  const match = tokensCss.match(new RegExp(`--${name}:\\s*(#[0-9a-f]{6})`, 'i'));
  if (!match) {
    throw new Error(`Không thấy token ${name}`);
  }
  return match[1];
}

function luminance(hex) {
  const channels = [1, 3, 5].map((start) => {
    const value = parseInt(hex.slice(start, start + 2), 16) / 255;
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrast(first, second) {
  const [light, dark] = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (light + 0.05) / (dark + 0.05);
}

describe('mã màu', () => {
  it('quét đủ mã nguồn', () => {
    const checked = Object.keys(SOURCES).filter(isChecked);

    expect(checked).toContain('src/styles/global.css');
    expect(checked).toContain('src/components/brand/motifs/Gear.jsx');
    expect(checked).toContain('index.html');
    expect(checked.length).toBeGreaterThan(30);
    expect(globalCss.length).toBeGreaterThan(1000);
    expect(tokensCss.length).toBeGreaterThan(100);
  });

  it('không có mã màu rời ngoài tokens.css', () => {
    const problems = Object.fromEntries(
      Object.entries(SOURCES)
        .filter(([path]) => isChecked(path))
        .map(([path, source]) => [path, findLooseColors(source)])
        .filter(([, found]) => found.length > 0),
    );

    expect(problems).toEqual({});
  });

  it.each(['color: #fff;', 'fill="#245890"', 'background: rgb(1 2 3);', 'color: white;'])(
    'bộ quét bắt được %s',
    (bad) => {
      expect(findLooseColors(bad)).not.toEqual([]);
    },
  );

  it.each(['href="#main"', 'var(--neu-primary)', 'white-space: nowrap;'])(
    'bộ quét không báo nhầm %s',
    (good) => {
      expect(findLooseColors(good)).toEqual([]);
    },
  );

  it('--neu-mid không được dùng cho chữ', () => {
    expect(globalCss).not.toMatch(/(?:^|[\s;{])color:\s*var\(--neu-mid\)/);
  });

  it('primary-dark tối hơn primary khoảng 12%', () => {
    const primary = token('neu-primary');
    const dark = token('neu-primary-dark');
    for (const start of [1, 3, 5]) {
      const ratio =
        parseInt(dark.slice(start, start + 2), 16) / parseInt(primary.slice(start, start + 2), 16);
      expect(ratio).toBeGreaterThan(0.86);
      expect(ratio).toBeLessThan(0.9);
    }
  });
});

describe('tỷ lệ tương phản', () => {
  it.each([
    ['chữ trắng trên primary', 'neu-white', 'neu-primary'],
    ['chữ trắng trên primary-dark', 'neu-white', 'neu-primary-dark'],
    ['primary trên tint', 'neu-primary', 'neu-tint'],
    ['chữ thường trên thẻ form', 'color-text', 'neu-white'],
    ['chữ phụ trên thẻ form', 'color-text-muted', 'neu-white'],
    ['chữ thường trên tint', 'color-text', 'neu-tint'],
    ['chữ phụ trên tint', 'color-text-muted', 'neu-tint'],
    ['lỗi trên nền đỏ nhạt', 'color-error', 'color-error-bg'],
    ['lỗi trên thẻ form', 'color-error', 'neu-white'],
    ['thành công trên thẻ', 'color-success', 'color-surface'],
  ])('%s đạt từ 4,5:1', (_name, foreground, background) => {
    expect(contrast(token(foreground), token(background))).toBeGreaterThanOrEqual(4.5);
  });

  it('công thức đúng: trắng trên đen là 21:1', () => {
    expect(contrast('#ffffff', '#000000')).toBeCloseTo(21, 5);
  });
});

describe('hiệu ứng mosaic', () => {
  it('tắt khi prefers-reduced-motion và không lặp', () => {
    const mosaicRule = globalCss.match(/\.motif-mosaic__cell \{[^}]*\}/)[0];
    const reduced = globalCss.match(
      /@media \(prefers-reduced-motion: reduce\) \{\s*\.motif-mosaic__cell \{\s*animation: none;/,
    );

    expect(reduced).not.toBeNull();
    expect(mosaicRule).not.toContain('infinite');
  });
});
