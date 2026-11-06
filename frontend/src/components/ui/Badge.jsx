/** tone: neutral, info, success, warning, danger, outline. */
export default function Badge({ tone = 'neutral', icon: Icon, className = '', children }) {
  return (
    <span className={`badge badge--${tone} ${className}`.trim()}>
      {Icon && <Icon size={14} aria-hidden="true" />}
      {children}
    </span>
  );
}
