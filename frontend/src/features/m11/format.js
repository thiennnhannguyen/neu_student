/** Điểm và GPA đến từ API dưới dạng chuỗi. Chỉ đổi dấu, không đổi sang số để không làm sai giá trị. */
export const NO_VALUE = '—';
export const NO_CODE = 'Chưa có mã';

export function formatDecimal(value) {
  if (value === null || value === undefined) {
    return NO_VALUE;
  }
  return String(value).replace('.', ',');
}

export function formatCount(value) {
  return value === null || value === undefined ? NO_VALUE : String(value);
}

export function formatSignedDecimal(value) {
  if (value === null || value === undefined) {
    return NO_VALUE;
  }
  const text = String(value);
  if (/^-?0+(\.0+)?$/.test(text)) {
    return formatDecimal(text.replace('-', ''));
  }
  return text.startsWith('-') ? formatDecimal(text) : `+${formatDecimal(text)}`;
}

export function formatSignedCount(value) {
  if (value === null || value === undefined) {
    return NO_VALUE;
  }
  return value > 0 ? `+${value}` : String(value);
}

export function formatDateTime(iso) {
  if (!iso) {
    return NO_VALUE;
  }
  const date = new Date(iso);
  const pad = (number) => String(number).padStart(2, '0');
  return (
    `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()} ` +
    `${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

export function courseCode(code) {
  return code ?? NO_CODE;
}

export function withQuery(path, params) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') {
      query.set(key, value);
    }
  }
  const text = query.toString();
  return text ? `${path}?${text}` : path;
}

/** Các kỳ có GPA trong danh sách của /gpa-trend, giữ thứ tự thời gian. */
export function gradedPoints(points) {
  return points.filter((point) => point.value !== null);
}
