import { Link } from 'react-router';
import { HEADER_STRIP } from '../brand/mosaicLayouts';
import MotifMosaic from '../brand/MotifMosaic';

export function Breadcrumb({ items }) {
  return (
    <nav aria-label="Vị trí trang" className="breadcrumb">
      <ol>
        {items.map((item) => (
          <li key={item.label}>
            {item.to ? <Link to={item.to}>{item.label}</Link> : <span>{item.label}</span>}
          </li>
        ))}
      </ol>
    </nav>
  );
}

export default function PageHeader({ title, description, breadcrumb, actions }) {
  return (
    <div className="page-header">
      <div className="page-header__text">
        {breadcrumb && <Breadcrumb items={breadcrumb} />}
        <h1>{title}</h1>
        {description && <p className="page-header__description">{description}</p>}
      </div>
      {actions && <div className="page-header__actions">{actions}</div>}
      <MotifMosaic {...HEADER_STRIP} className="page-header__motif" />
    </div>
  );
}
