import { ILLUSTRATION } from '../brand/mosaicLayouts';
import MotifMosaic from '../brand/MotifMosaic';

export default function EmptyState({ title, description, action, heading: Heading = 'h2', role }) {
  return (
    <div className="empty-block" role={role}>
      <MotifMosaic {...ILLUSTRATION} className="empty-block__art" />
      <Heading className="empty-block__title">{title}</Heading>
      {description && <p className="empty-block__description">{description}</p>}
      {action && <div className="empty-block__action">{action}</div>}
    </div>
  );
}
