import { describe, expect, it } from 'vitest';
import {
  courseCode,
  formatCount,
  formatDecimal,
  formatSignedCount,
  formatSignedDecimal,
  withQuery,
} from './format';
import { carrySearch } from './scopeQuery';

describe('định dạng số', () => {
  it.each([
    ['3.11', '3,11'],
    ['2.88', '2,88'],
    ['4.00', '4,00'],
    ['10', '10'],
    [null, '—'],
    [undefined, '—'],
  ])('%s -> %s', (value, expected) => {
    expect(formatDecimal(value)).toBe(expected);
  });

  it('giữ nguyên chữ số, không làm tròn hay bỏ số 0', () => {
    expect(formatDecimal('2.50')).toBe('2,50');
    expect(formatDecimal('0.10')).toBe('0,10');
    expect(formatDecimal('16.125')).toBe('16,125');
  });

  it('số nguyên và null', () => {
    expect(formatCount(0)).toBe('0');
    expect(formatCount(null)).toBe('—');
  });

  it.each([
    ['0.25', '+0,25'],
    ['-0.25', '-0,25'],
    ['0.00', '0,00'],
    ['-0.00', '0,00'],
    [null, '—'],
  ])('chênh lệch GPA %s -> %s', (value, expected) => {
    expect(formatSignedDecimal(value)).toBe(expected);
  });

  it.each([
    [3, '+3'],
    [-1, '-1'],
    [0, '0'],
    [null, '—'],
  ])('chênh lệch đếm %s -> %s', (value, expected) => {
    expect(formatSignedCount(value)).toBe(expected);
  });

  it('mã môn null hiện "Chưa có mã"', () => {
    expect(courseCode(null)).toBe('Chưa có mã');
    expect(courseCode('CNT101')).toBe('CNT101');
  });

  it('bỏ tham số rỗng khi ghép URL', () => {
    expect(withQuery('/x', { a: 'S1', b: null, c: '', d: undefined })).toBe('/x?a=S1');
    expect(withQuery('/x', {})).toBe('/x');
  });
});

describe('sidebar mang theo tham số', () => {
  it.each([
    ['?student=SV01&semester=S4', '?student=SV01&semester=S4'],
    ['?student=SV01&semester=all', '?student=SV01'],
    ['?semester=all', ''],
    ['?semester=S4&status=failed&q=a&page=2', '?semester=S4'],
    ['', ''],
  ])('%s -> "%s"', (search, expected) => {
    expect(carrySearch(search)).toBe(expected);
  });
});
