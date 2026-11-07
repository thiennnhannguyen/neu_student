import { percentText } from './labels';

const RADIUS = 42;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/** Vòng tiến độ. Số nằm giữa là chữ thật, mẫu số 0 hiện "—" và không vẽ cung. */
export default function ProgressRing({ percent, label, size = 'lg' }) {
  const filled = ((percent ?? 0) / 100) * CIRCUMFERENCE;
  return (
    <div className={`progress-ring progress-ring--${size}`}>
      <div className="progress-ring__chart">
        <svg viewBox="0 0 100 100" aria-hidden="true" focusable="false">
          <circle className="progress-ring__track" cx="50" cy="50" r={RADIUS} />
          <circle
            className="progress-ring__fill"
            cx="50"
            cy="50"
            r={RADIUS}
            strokeDasharray={`${filled} ${CIRCUMFERENCE}`}
            transform="rotate(-90 50 50)"
          />
        </svg>
        <strong className="progress-ring__value">{percentText(percent)}</strong>
      </div>
      <span className="progress-ring__label">{label}</span>
    </div>
  );
}
