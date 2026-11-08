import { Link } from 'react-router';
import StatusChip from './StatusChip';

/**
 * Có `to` thì cả thẻ bấm được; nút "i" truyền qua `info` nằm trên lớp liên kết.
 * `status` là watch hoặc warning: viền trái và nhãn cạnh giá trị, nên màu không là tín hiệu duy nhất.
 * `hint` là một dòng hoặc mảng tối đa 2 dòng phụ; dòng rỗng bị bỏ qua.
 */
export default function MetricCard({
  label,
  value,
  hint,
  info,
  footer,
  to,
  emphasis = false,
  status,
}) {
  const classes = ['metric-card'];
  if (emphasis) {
    classes.push('metric-card--emphasis');
  }
  if (status) {
    classes.push(`metric-card--${status}`);
  }
  return (
    <article className={classes.join(' ')}>
      <div className="metric-card__head">
        {to ? (
          <Link to={to} className="metric-card__link">
            {label}
          </Link>
        ) : (
          <span className="metric-card__label">{label}</span>
        )}
        {info}
      </div>
      <div className="metric-card__value-row">
        <p className="metric-card__value">{value}</p>
        {status && <StatusChip status={status} />}
      </div>
      {(Array.isArray(hint) ? hint : [hint]).filter(Boolean).map((line, index) => (
        <p key={index} className="metric-card__detail">
          {line}
        </p>
      ))}
      {footer}
    </article>
  );
}
