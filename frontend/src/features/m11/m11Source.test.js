import { readdirSync, readFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import process from 'node:process';
import { describe, expect, it } from 'vitest';

const SRC = join(process.cwd(), 'src');
const CHART_FILE = 'features/m11/GpaTrendChart.jsx';
const SOURCES = readdirSync(SRC, { recursive: true })
  .filter(
    (name) => /\.jsx?$/.test(name) && !/\.test\.jsx?$/.test(name) && name !== 'test/fakeApi.js',
  )
  .map((name) => relative(SRC, join(SRC, name)))
  .filter((name) => name !== 'features/m11/testData.js')
  // Họa tiết SVG có toFixed cho tọa độ hình vẽ, không liên quan tới điểm.
  .filter((name) => !name.startsWith('components/brand/'));

const FIELD = '(?:score|gpa|grade|value|numerator|delta|raw|plotted)';
const NUMERIC_ON_FIELD = new RegExp(
  `(?:parseFloat|Number|parseInt)\\([^)]*${FIELD}|\\+\\s*[\\w.]*${FIELD}\\b(?=\\s*[;,)])`,
  'i',
);

export function findNumericConversions(source) {
  const anyFloat = source.match(/parseFloat\(|\bNumber\(|toFixed\(/g) ?? [];
  const onField = NUMERIC_ON_FIELD.test(source) ? ['áp lên trường điểm'] : [];
  return [...anyFloat, ...onField];
}

describe('điểm và GPA không đi qua số khi hiển thị (Q78)', () => {
  it('ngoài GpaTrendChart, không có parseFloat, Number(), toFixed() trong mã nguồn', () => {
    const problems = {};
    for (const name of SOURCES) {
      if (name === CHART_FILE) {
        continue;
      }
      const found = findNumericConversions(readFileSync(join(SRC, name), 'utf8'));
      if (found.length) {
        problems[name] = found;
      }
    }
    expect(problems).toEqual({});
  });

  it('GpaTrendChart chỉ đổi sang số đúng 1 chỗ, và chỉ cho giá trị vẽ', () => {
    const source = readFileSync(join(SRC, CHART_FILE), 'utf8');

    expect(source.match(/\bNumber\(/g)).toHaveLength(1);
    expect(source).toMatch(/plotted: point\.value === null \? null : Number\(point\.value\)/);
    expect(source).not.toMatch(/parseFloat\(|toFixed\(/);
    expect(source).toMatch(/formatDecimal\(point\.raw\)/);
    expect(source).toMatch(/formatDecimal\(point\.value\)/);
  });

  it.each(['parseFloat(row.score_10)', 'Number(data.gpa)', 'x.toFixed(2)', 'const a = +row.gpa;'])(
    'bộ quét bắt được %s',
    (bad) => {
      expect(findNumericConversions(bad).length).toBeGreaterThan(0);
    },
  );

  it.each(["parseInt(params.get('page') ?? '1', 10)", "formatDecimal('3.11')"])(
    'bộ quét không báo nhầm %s',
    (good) => {
      expect(findNumericConversions(good)).toEqual([]);
    },
  );
});
