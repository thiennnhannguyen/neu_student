/**
 * Bổ sung D-309 (phản hồi CR-11, mục B1): DEMO_TODAY chỉ dời NGÀY nghiệp vụ. Giờ hệ thống (lúc
 * tính số liệu, lúc cấp chứng chỉ, lúc nộp minh chứng, giờ được làm lại bài) vẫn là giờ thật, nên
 * khi có ngày demo thì ghi rõ "(giờ thật)" để không lệch với "Ngày hệ thống".
 */
import { useAuth } from '../auth/AuthContext';
import { formatDateTime } from './format';

export const REAL_TIME_NOTE = '(giờ thật)';

/** Ngày demo (YYYY-MM-DD) nếu máy chủ đặt DEMO_TODAY; null khi chạy theo ngày thật. */
export function useDemoToday() {
  return useAuth()?.identity?.demo_today ?? null;
}

/** Chữ giờ hệ thống; thêm "(giờ thật)" khi có ngày demo. */
export function systemTimeText(iso, demoToday) {
  const text = formatDateTime(iso);
  return iso && demoToday ? `${text} ${REAL_TIME_NOTE}` : text;
}

export function SystemTime({ iso }) {
  return systemTimeText(iso, useDemoToday());
}

/** Ghi chú " (giờ thật)" đặt ngay sau một giờ hệ thống đã định dạng sẵn ở chỗ khác. */
export function RealTimeNote() {
  return useDemoToday() ? ` ${REAL_TIME_NOTE}` : null;
}
