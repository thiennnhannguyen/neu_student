import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router';
import AppLayout from './components/AppLayout';
import ComingSoonPage from './components/ComingSoonPage';
import NotFoundPage from './components/NotFoundPage';
import { M11_READERS, MENU_GROUPS, PENDING_ITEMS } from './components/menu';
import AuditLogPage from './features/admin/AuditLogPage';
import { AuthProvider } from './features/auth/AuthContext';
import LoginPage from './features/auth/LoginPage';
import ProtectedRoute from './features/auth/ProtectedRoute';
import RoleRoute from './features/auth/RoleRoute';
import HomeRoute from './features/m11/HomeRoute';
import ResultsPage from './features/m11/ResultsPage';
import RisksPage from './features/m11/RisksPage';
import CareerDetailPage from './features/m12/CareerDetailPage';
import CareersPage from './features/m12/CareersPage';
import EvidenceReviewPage from './features/m12/evidence/EvidenceReviewPage';
import PlanDiffPage from './features/m12/plan/PlanDiffPage';
import PlanPage from './features/m12/plan/PlanPage';
import SupportDetailPage from './features/m12/support/SupportDetailPage';
import SupportListPage from './features/m12/support/SupportListPage';
import ImprovementPlanPage from './features/m11/ImprovementPlanPage';
import ProfilePage from './features/profile/ProfilePage';

// Recharts khá nặng nên chỉ tải khi mở trang Phân tích.
const AnalysisPage = lazy(() => import('./features/m11/AnalysisPage'));

// Chỉ có khi chạy dev; bản production loại hẳn, npm run check:bundle kiểm tra.
const StyleguidePage = import.meta.env.DEV
  ? lazy(() => import('./features/dev/StyleguidePage'))
  : null;
const IllustrationsSheet = import.meta.env.DEV
  ? lazy(() => import('./features/m12/illustrations/IllustrationsSheet'))
  : null;

const IMPLEMENTED_PAGES = {
  '/ho-so': <ProfilePage />,
  '/m11/ket-qua': <ResultsPage />,
  '/m11/phan-tich': (
    <Suspense fallback={<p role="status">Đang tải trang...</p>}>
      <AnalysisPage />
    </Suspense>
  ),
  '/m11/canh-bao': <RisksPage />,
  '/m12/dinh-huong': <CareersPage />,
  '/m12/ke-hoach': <PlanPage />,
  '/m12/duyet-minh-chung': <EvidenceReviewPage />,
  '/m12/yeu-cau-ho-tro': <SupportListPage />,
  '/quan-tri/nhat-ky': <AuditLogPage />,
};

const RESTRICTED_ITEMS = MENU_GROUPS.flatMap((group) => group.items).filter(
  (item) => item.path in IMPLEMENTED_PAGES,
);

/** Trang Xem tất cả cũ nay là lưới thẻ; giữ các tham số của đường dẫn cũ, như sinh viên đang chọn. */
function OldAllCareersRedirect() {
  const { search } = useLocation();
  return <Navigate replace to={`/m12/dinh-huong${search}`} />;
}

export default function AppRoutes() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        {IllustrationsSheet && (
          <Route
            path="/dev/illustrations"
            element={
              <Suspense fallback={<p role="status">Đang tải trang...</p>}>
                <IllustrationsSheet />
              </Suspense>
            }
          />
        )}
        {StyleguidePage && (
          <Route
            path="/dev/styleguide"
            element={
              <Suspense fallback={<p role="status">Đang tải trang...</p>}>
                <StyleguidePage />
              </Suspense>
            }
          />
        )}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomeRoute />} />
            {RESTRICTED_ITEMS.map((item) => (
              <Route key={item.path} element={<RoleRoute roles={item.roles} />}>
                <Route path={item.path} element={IMPLEMENTED_PAGES[item.path]} />
              </Route>
            ))}
            <Route element={<RoleRoute roles={M11_READERS} />}>
              <Route path="/m12/dinh-huong/tat-ca" element={<OldAllCareersRedirect />} />
              <Route path="/m12/dinh-huong/nghe/:slug" element={<CareerDetailPage />} />
              <Route path="/m12/ke-hoach/khac-biet" element={<PlanDiffPage />} />
              <Route path="/m11/canh-bao/ke-hoach" element={<ImprovementPlanPage />} />
            </Route>
            <Route path="/m12/yeu-cau-ho-tro/:id" element={<SupportDetailPage />} />
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
