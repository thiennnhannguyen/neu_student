import { Star } from 'lucide-react';

export const GOAL_LABEL = 'Mục tiêu chính của bạn';

/** Ngôi sao đánh dấu nghề là mục tiêu chính (CR-07), thay nhãn chữ "Mục tiêu của bạn". */
export default function GoalStar({ className, size = 16 }) {
  return (
    <span
      role="img"
      aria-label={GOAL_LABEL}
      title={GOAL_LABEL}
      className={`goal-star ${className}`}
    >
      <Star size={size} fill="currentColor" aria-hidden="true" />
    </span>
  );
}
