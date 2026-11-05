import { Route, Routes } from 'react-router';
import AppLayout from './components/AppLayout';
import ComingSoonPage from './components/ComingSoonPage';
import HomePage from './components/HomePage';
import NotFoundPage from './components/NotFoundPage';
import { MENU_GROUPS, PENDING_ITEMS } from './components/menu';
import AuditLogPage from './features/admin/AuditLogPage';
import { AuthProvider } from './features/auth/AuthContext';
import LoginPage from './features/auth/LoginPage';
import ProtectedRoute from './features/auth/ProtectedRoute';
import RoleRoute from './features/auth/RoleRoute';
import ProfilePage from './features/profile/ProfilePage';

const IMPLEMENTED_PAGES = {
  '/ho-so': <ProfilePage />,
  '/quan-tri/nhat-ky': <AuditLogPage />,
};

const RESTRICTED_ITEMS = MENU_GROUPS.flatMap((group) => group.items).filter(
  (item) => item.path in IMPLEMENTED_PAGES,
);

export default function AppRoutes() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomePage />} />
            {RESTRICTED_ITEMS.map((item) => (
              <Route key={item.path} element={<RoleRoute roles={item.roles} />}>
                <Route path={item.path} element={IMPLEMENTED_PAGES[item.path]} />
              </Route>
            ))}
            {PENDING_ITEMS.map((item) => (
              <Route key={item.path} element={<RoleRoute roles={item.roles} />}>
                <Route path={item.path} element={<ComingSoonPage title={item.label} />} />
              </Route>
            ))}
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  );
}
