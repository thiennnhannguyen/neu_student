import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { useRef } from 'react';
import { NavLink, useLocation } from 'react-router';
import { useAuth } from '../features/auth/AuthContext';
import { carrySearch } from '../features/m11/scopeQuery';
import BrandLogo from './BrandLogo';
import { SIDEBAR_BAND } from './brand/mosaicLayouts';
import MotifMosaic from './brand/MotifMosaic';
import { menuForRole, ROLE_LABELS } from './menu';
import Avatar from './ui/Avatar';
import useFocusTrap from './ui/useFocusTrap';

export default function Sidebar({ open, onClose, collapsed, onToggleCollapsed }) {
  const { role, identity } = useAuth();
  const { search } = useLocation();
  const carried = carrySearch(search);
  const navRef = useRef(null);
  useFocusTrap(navRef, open, onClose);

  return (
    <nav
      ref={navRef}
      id="app-sidebar"
      className={`sidebar${open ? ' sidebar--open' : ''}`}
      aria-label="Menu chính"
    >
      <div className="sidebar__brand">
        <BrandLogo className="sidebar__logo" />
        <div className="sidebar__brand-text">
          <span className="sidebar__brand-name">NEU Student</span>
          <span className="sidebar__brand-sub">Learning Platform</span>
        </div>
      </div>
      <div className="sidebar__menu">
        {menuForRole(role).map((group) => (
          <div key={group.id} className="sidebar__group">
            {group.title && <p className="sidebar__title">{group.title}</p>}
            <ul>
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <li key={item.path}>
                    <NavLink
                      to={`${item.path}${carried}`}
                      end
                      data-tooltip={item.label}
                      onClick={onClose}
                    >
                      <Icon size={20} aria-hidden="true" />
                      <span className="sidebar__label">{item.label}</span>
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
      <button
        type="button"
        className="sidebar__collapse"
        aria-pressed={collapsed}
        aria-label={collapsed ? 'Mở rộng menu' : 'Thu gọn menu'}
        data-tooltip={collapsed ? 'Mở rộng menu' : 'Thu gọn menu'}
        onClick={onToggleCollapsed}
      >
        {collapsed ? (
          <PanelLeftOpen size={20} aria-hidden="true" />
        ) : (
          <PanelLeftClose size={20} aria-hidden="true" />
        )}
        <span className="sidebar__label" aria-hidden="true">
          Thu gọn
        </span>
      </button>
      <MotifMosaic {...SIDEBAR_BAND} className="sidebar__mosaic" />
      <div className="sidebar__user">
        <Avatar name={identity.user.full_name} size="sm" />
        <div className="sidebar__user-text">
          <span>{identity.user.full_name}</span>
          <span className="sidebar__brand-sub">{ROLE_LABELS[role]}</span>
        </div>
      </div>
    </nav>
  );
}
