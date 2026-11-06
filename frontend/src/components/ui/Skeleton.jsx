export default function Skeleton({ width = '100%', height = 16, className = '' }) {
  return (
    <span className={`skeleton ${className}`.trim()} aria-hidden="true" style={{ width, height }} />
  );
}
