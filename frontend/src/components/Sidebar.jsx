import { NavLink } from 'react-router';
import { useAuth } from '../features/auth/AuthContext';
import { menuForRole } from './menu';

export default function Sidebar({ open, onNavigate }) {
  const { role } = useAuth();

  return (
    <nav
      id="app-sidebar"
      className={`sidebar${open ? ' sidebar--open' : ''}`}
      aria-label="Menu chính"
    >
      {menuForRole(role).map((group) => (
        <div key={group.title ?? 'chung'} className="sidebar__group">
          {group.title && <p className="sidebar__title">{group.title}</p>}
          <ul>
            {group.items.map((item) => (
              <li key={item.path}>
                <NavLink to={item.path} end onClick={onNavigate}>
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}
