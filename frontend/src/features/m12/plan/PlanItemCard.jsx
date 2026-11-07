import { Target } from 'lucide-react';
import { Badge } from '../../../components/ui';
import { NO_CODE } from '../labels';
import {
  alignmentLabel,
  ASSUMED_POSITION,
  CONFIRMED,
  DU_KIEN,
  PENDING_RESULT,
  PRIMARY_CAREER,
} from './labels';

/** Thẻ một môn trong cột kỳ. Cả thẻ là nút mở panel. */
export default function PlanItemCard({ item, selected, onSelect }) {
  const { course } = item;
  const alignment = alignmentLabel(item.semester_alignment);
  return (
    <button
      type="button"
      className={`plan-card${item.is_primary_career ? ' plan-card--primary' : ''}`}
      aria-pressed={selected}
      onClick={() => onSelect(item)}
    >
      <span className="plan-card__title">{course.name}</span>
      <span className="plan-card__meta">
        <span>{course.code ?? NO_CODE}</span>
        <span>{course.credits} tín chỉ</span>
      </span>
      {item.is_primary_career && (
        <span className="plan-card__career">
          <Target size={14} aria-hidden="true" />
          {PRIMARY_CAREER}
        </span>
      )}
      <span className="plan-card__chips">
        <Badge tone={item.confidence === 'confirmed' ? 'success' : 'neutral'}>
          {item.confidence === 'confirmed' ? CONFIRMED : DU_KIEN}
        </Badge>
        {item.depends_on_pending_result && <Badge tone="warning">{PENDING_RESULT}</Badge>}
        {alignment && (
          <Badge tone={item.semester_alignment.kind === 'on_time' ? 'info' : 'warning'}>
            {alignment}
          </Badge>
        )}
      </span>
      {item.assumed_position && <span className="plan-card__assumed">{ASSUMED_POSITION}</span>}
    </button>
  );
}
