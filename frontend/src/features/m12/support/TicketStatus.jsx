import { Badge, CheckBadge } from '../../../components/ui';
import { CircleDot, Clock, MessageCircleQuestion } from 'lucide-react';

export const TICKET_STATUSES = [
  { value: 'new', label: 'Mới', tone: 'info', icon: CircleDot },
  { value: 'in_progress', label: 'Đang xử lý', tone: 'neutral', icon: Clock },
  { value: 'need_info', label: 'Cần bổ sung', tone: 'warning', icon: MessageCircleQuestion },
  { value: 'done', label: 'Hoàn thành', tone: 'success', icon: CheckBadge },
];

export function statusLabel(status) {
  return TICKET_STATUSES.find((item) => item.value === status).label;
}

export default function TicketStatus({ status }) {
  const item = TICKET_STATUSES.find((row) => row.value === status);
  return (
    <Badge tone={item.tone} icon={item.icon}>
      {item.label}
    </Badge>
  );
}
