/**
 * Điểm dự kiến và mức cảnh báo từng môn (CR-13, D-314). Số do backend tính, giao diện chỉ hiển thị
 * chuỗi (formatDecimal), không đổi sang số (Q78).
 */
import { AlertTriangle, XCircle } from 'lucide-react';
import { formatDecimal } from './format';

export const LEVELS = {
  barred: { label: 'Không đủ điều kiện dự thi', icon: XCircle, tone: 'danger' },
  high: { label: 'Nguy cơ cao', icon: XCircle, tone: 'danger' },
  watch: { label: 'Cần chú ý', icon: AlertTriangle, tone: 'warning' },
  ok: { label: 'Ổn', icon: null, tone: 'success' },
  insufficient: { label: 'Chưa đủ dữ liệu', icon: null, tone: 'neutral' },
};

export const CONFIDENCE = { low: 'Thấp', medium: 'Trung bình', high: 'Cao' };

export const DISCLAIMER = 'Dự kiến chỉ mang tính tham khảo, dựa trên dữ liệu mô phỏng.';

/** Icon kèm chữ, không có khối màu. Mức Ổn và Chưa đủ dữ liệu không có icon. */
export function LevelMark({ level }) {
  const item = LEVELS[level] ?? LEVELS.insufficient;
  const Icon = item.icon;
  return (
    <span className={`level-mark status-icon--${item.tone}`}>
      {Icon && <Icon size={16} aria-hidden="true" />}
      {item.label}
    </span>
  );
}

/** "6,78 C+", hoặc dòng chữ khi không có điểm. */
export function scoreText(prediction) {
  if (prediction.level === 'barred') {
    return LEVELS.barred.label;
  }
  if (prediction.score === null) {
    return LEVELS.insufficient.label;
  }
  return `${formatDecimal(prediction.score)} ${prediction.letter ?? ''}`.trim();
}

export function rangeText(range) {
  return range ? `${formatDecimal(range.low)}–${formatDecimal(range.high)}` : '—';
}

/** Ô "Điểm dự kiến" của bảng: số và điểm chữ, kèm icon và chữ khi có cảnh báo. */
export function PredictionCell({ prediction }) {
  if (prediction.level === 'barred') {
    return <LevelMark level="barred" />;
  }
  const warned = ['high', 'watch'].includes(prediction.level);
  return (
    <span className="prediction-cell">
      <span className="prediction-cell__score">{scoreText(prediction)}</span>
      {warned && <LevelMark level={prediction.level} />}
    </span>
  );
}
