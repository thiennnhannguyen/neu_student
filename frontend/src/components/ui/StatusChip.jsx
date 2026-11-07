import {
  AlertTriangle,
  Ban,
  Check,
  CheckCheck,
  Circle,
  CircleHelp,
  Clock,
  Eye,
  FileQuestionMark,
  Hourglass,
  Medal,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  X,
} from 'lucide-react';
import Badge from './Badge';

/** 6 trạng thái môn (Q64), 2 trạng thái kỹ năng, các mức cảnh báo và nhóm môn. Luôn có biểu tượng và chữ, không chỉ dựa vào màu. */
export const STATUS_CHIPS = {
  done: { label: 'Đạt', icon: Check, tone: 'success' },
  done_via_equivalency: { label: 'Đạt qua tương đương', icon: CheckCheck, tone: 'success' },
  exempt: { label: 'Miễn', icon: Medal, tone: 'success' },
  in_progress: { label: 'Đang học', icon: Clock, tone: 'info' },
  failed: { label: 'Chưa đạt', icon: X, tone: 'danger' },
  not_started: { label: 'Chưa học', icon: Circle, tone: 'neutral' },
  pending: { label: 'Chờ duyệt', icon: Hourglass, tone: 'warning' },
  no_evidence: { label: 'Chưa có minh chứng', icon: FileQuestionMark, tone: 'neutral' },
  not_in_program: { label: 'Không có trong CTĐT ngành bạn', icon: Ban, tone: 'neutral' },
  normal: { label: 'Bình thường', icon: ShieldCheck, tone: 'success' },
  watch: { label: 'Chú ý', icon: Eye, tone: 'warning' },
  warning: { label: 'Cảnh báo', icon: AlertTriangle, tone: 'danger' },
  insufficient_data: { label: 'Chưa đủ dữ liệu', icon: CircleHelp, tone: 'neutral' },
  not_applicable: { label: 'Không áp dụng', icon: Ban, tone: 'neutral' },
  strong: { label: 'Điểm mạnh', icon: TrendingUp, tone: 'success' },
  weak: { label: 'Điểm yếu', icon: TrendingDown, tone: 'warning' },
};

export default function StatusChip({ status, size = 'md' }) {
  const chip = STATUS_CHIPS[status] ?? { label: status, icon: CircleHelp, tone: 'neutral' };
  return (
    <Badge tone={chip.tone} icon={chip.icon} className={`status-chip status-chip--${size}`}>
      {chip.label}
    </Badge>
  );
}
