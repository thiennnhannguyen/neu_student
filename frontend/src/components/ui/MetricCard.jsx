import { Link } from 'react-router';

/** Có `to` thì cả thẻ bấm được; nút "i" truyền qua `info` nằm trên lớp liên kết. */
export default function MetricCard({ label, value, hint, info, footer, to, emphasis = false }) {
  return (
    <article className={`metric-card${emphasis ? ' metric-card--emphasis' : ''}`}>
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
      <p className="metric-card__value">{value}</p>
      {hint && <p className="metric-card__detail">{hint}</p>}
      {footer}
    </article>
  );
}
