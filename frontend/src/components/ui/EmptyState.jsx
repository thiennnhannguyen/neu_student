import { ILLUSTRATION } from '../brand/mosaicLayouts';
import MotifMosaic from '../brand/MotifMosaic';

/** compact: dùng bên trong Card hoặc panel, không có khung và họa tiết riêng. */
export default function EmptyState({
  title,
  description,
  action,
  heading: Heading = 'h2',
  role,
  compact = false,
}) {
  return (
    <div className={`empty-block${compact ? ' empty-block--compact' : ''}`} role={role}>
      {!compact && <MotifMosaic {...ILLUSTRATION} className="empty-block__art" />}
      <Heading className="empty-block__title">{title}</Heading>
      {description && <p className="empty-block__description">{description}</p>}
      {action && <div className="empty-block__action">{action}</div>}
    </div>
  );
}
