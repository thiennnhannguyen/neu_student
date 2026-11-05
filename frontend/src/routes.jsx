import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router';
import AppLayout from './components/AppLayout';
import ComingSoonPage from './components/ComingSoonPage';
import NotFoundPage from './components/NotFoundPage';
import { MENU_GROUPS, PENDING_ITEMS } from './components/menu';
import AuditLogPage from './features/admin/AuditLogPage';
import { AuthProvider } from './features/auth/AuthContext';
import LoginPage from './features/auth/LoginPage';
import ProtectedRoute from './features/auth/ProtectedRoute';
import RoleRoute from './features/auth/RoleRoute';
import HomeRoute from './features/m11/HomeRoute';
import ResultsPage from './features/m11/ResultsPage';
import RisksPage from './features/m11/RisksPage';
import ProfilePage from './features/profile/ProfilePage';

// Recharts khá nặng nên chỉ tải khi mở trang Phân tích.
const AnalysisPage = lazy(() => import('./features/m11/AnalysisPage'));

const IMPLEMENTED_PAGES = {
  '/ho-so': <ProfilePage />,
  '/m11/ket-qua': <ResultsPage />,
  '/m11/phan-tich': (
    <Suspense fallback={<p role="status">Đang tải trang...</p>}>
      <AnalysisPage />
    </Suspense>
  ),
  '/m11/canh-bao': <RisksPage />,
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
            <Route path="/" element={<HomeRoute />} />
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
