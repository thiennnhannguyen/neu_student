import {
  AlertTriangle,
  Ban,
  Check,
  Circle,
  CircleHelp,
  Clock,
  ClockAlert,
  FileQuestionMark,
  Hourglass,
  Medal,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  Link2,
  X,
  XCircle,
} from 'lucide-react';

/**
 * Trạng thái môn và kỹ năng chỉ có biểu tượng (kèm aria-label, tooltip, chú giải ở đầu danh sách).
 * Mức cảnh báo và nhóm môn có biểu tượng và chữ thường. Không có khối nền màu.
 */
export const STATUS_CHIPS = {
  done: { label: 'Đạt', icon: Check, tone: 'success' },
  done_via_equivalency: {
    label: 'Đạt qua tương đương',
    icon: Check,
    tone: 'success',
    linked: true,
  },
  exempt: { label: 'Miễn', icon: Medal, tone: 'success' },
  in_progress: { label: 'Đang học', icon: Clock, tone: 'info' },
  failed: { label: 'Chưa đạt', icon: X, tone: 'danger' },
  not_started: { label: 'Chưa học', icon: Circle, tone: 'neutral' },
  pending: { label: 'Chờ duyệt', icon: Hourglass, tone: 'warning' },
  no_evidence: { label: 'Chưa có minh chứng', icon: FileQuestionMark, tone: 'neutral' },
  not_in_program: { label: 'Không có trong CTĐT ngành bạn', icon: Ban, tone: 'neutral' },
  // D-315: một bộ từ chỉ mức cho Cảnh báo học vụ và môn học; icon trùng bảng môn (⚠ nhẹ, ✗ nặng).
  normal: { label: 'Ổn', icon: ShieldCheck, tone: 'success' },
  watch: { label: 'Cần chú ý', icon: AlertTriangle, tone: 'warning' },
  warning: { label: 'Nguy cơ cao', icon: XCircle, tone: 'danger' },
  insufficient_data: { label: 'Chưa đủ dữ liệu', icon: CircleHelp, tone: 'neutral' },
  not_applicable: { label: 'Không áp dụng', icon: Ban, tone: 'neutral' },
  strong: { label: 'Điểm mạnh', icon: TrendingUp, tone: 'success' },
  weak: { label: 'Điểm yếu', icon: TrendingDown, tone: 'warning' },
  // Bài tập LMS (D-309): biểu tượng kèm chữ, không khối màu.
  lms_graded: { label: 'Đã chấm', icon: Check, tone: 'success' },
  lms_pending: { label: 'Chờ chấm', icon: Hourglass, tone: 'info' },
  lms_overdue: { label: 'Quá hạn chưa nộp', icon: X, tone: 'danger' },
  lms_not_due: { label: 'Chưa đến hạn', icon: Circle, tone: 'neutral' },
  lms_late: { label: 'Nộp muộn', icon: ClockAlert, tone: 'warning' },
};

const ICON_ONLY = new Set([
  'done',
  'done_via_equivalency',
  'exempt',
  'in_progress',
  'failed',
  'not_started',
  'pending',
  'no_evidence',
]);

function StatusIcon({ chip }) {
  const Icon = chip.icon;
  return (
    <>
      <Icon size={16} aria-hidden="true" />
      {chip.linked && <Link2 size={10} aria-hidden="true" className="status-icon__link" />}
    </>
  );
}

/** `iconOnly` ép kiểu chỉ icon (có aria-label, tooltip) khi chữ đã đứng ngay cạnh, vd lý do cảnh báo. */
export default function StatusChip({ status, iconOnly = false }) {
  const chip = STATUS_CHIPS[status] ?? { label: status, icon: CircleHelp, tone: 'neutral' };
  if (iconOnly || ICON_ONLY.has(status)) {
    return (
      <span
        role="img"
        aria-label={chip.label}
        title={chip.label}
        className={`status-icon status-icon--${chip.tone}`}
      >
        <StatusIcon chip={chip} />
      </span>
    );
  }
  const Icon = chip.icon;
  return (
    <span className={`status-text status-icon--${chip.tone}`}>
      <Icon size={16} aria-hidden="true" />
      {chip.label}
    </span>
  );
}

/** Chú giải biểu tượng, đặt ở đầu mỗi danh sách có trạng thái. */
export function StatusLegend({ statuses }) {
  return (
    <ul className="status-legend" aria-label="Chú giải trạng thái">
      {statuses.map((status) => (
        <li key={status}>
          <span className={`status-icon status-icon--${STATUS_CHIPS[status].tone}`}>
            <StatusIcon chip={STATUS_CHIPS[status]} />
          </span>
          {STATUS_CHIPS[status].label}
        </li>
      ))}
    </ul>
  );
}
