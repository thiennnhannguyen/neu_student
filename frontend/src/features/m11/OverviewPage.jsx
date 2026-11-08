import { useLocation } from 'react-router';
import { ROLE_LABELS } from '../../components/menu';
import ShortcutGrid from '../../components/ShortcutGrid';
import { EmptyState, MetricCard, Skeleton } from '../../components/ui';
import WelcomeCard from '../../components/WelcomeCard';
import { useAuth } from '../auth/AuthContext';
import { formatCount, formatDecimal, withQuery } from './format';
import M11Page from './M11Page';
import { useM11ScopeValue } from './M11ScopeContext';
import MetricInfo from './MetricInfo';
import { CreditPie, GpaBars } from './OverviewCharts';
import { carrySearch } from './scopeQuery';
import SemesterFilter from './SemesterFilter';
import useApiResource from './useApiResource';
import { ResourceView } from './ui';

/** Tổng quan theo ảnh mẫu (CR-08, D-306): thẻ chỉ có nhãn, nút "i" và số, không có dòng phụ. */
function OverviewMetric({ title, metricKey, value, to, studentId }) {
  return (
    <MetricCard
      label={title}
      value={value}
      to={to}
      info={<MetricInfo metricKey={metricKey} label={title} studentId={studentId} />}
    />
  );
}

function OverviewSkeleton() {
  return (
    <>
      <p role="status" className="visually-hidden">
        Đang tải tổng quan...
      </p>
      <div className="overview-stats">
        <div className="overview-cards metric-grid">
          {[1, 2, 3, 4].map((key) => (
            <div key={key} className="metric-card metric-card--skeleton">
              <Skeleton width="60%" />
              <Skeleton width="40%" height={36} />
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

/** Trang đích của thẻ "Số môn chưa đạt": đúng tập môn mà thẻ đếm, tính đến kỳ đang xem (D-297). */
export function failedListLink(search, semesterId) {
  const params = new URLSearchParams(carrySearch(search));
  if (semesterId) {
    params.set('semester', semesterId);
  }
  params.set('view', 'failed');
  return `/m11/ket-qua?${params.toString()}`;
}

function ChartPanel({ id, title, resource, errorText, children }) {
  return (
    <section className="overview-chart" aria-labelledby={id}>
      <h2 id={id} className="visually-hidden">
        {title}
      </h2>
      <ResourceView
        resource={resource}
        loadingText={`Đang tải ${title.toLowerCase()}...`}
        errorText={errorText}
        compact
      >
        {children}
      </ResourceView>
    </section>
  );
}

function OverviewContent({ scope }) {
  const { search } = useLocation();
  const resource = useApiResource(withQuery('/api/m11/overview', scope.query));
  const credits = useApiResource(withQuery('/api/m11/credits', scope.query));
  const trend = useApiResource(withQuery('/api/m11/gpa-trend', scope.query));
  const link = (path) => `${path}${carrySearch(search)}`;
  if (resource.status === 'loading') {
    return <OverviewSkeleton />;
  }
  return (
    <ResourceView
      resource={resource}
      loadingText="Đang tải tổng quan..."
      errorText="Không tải được tổng quan"
    >
      {(data) => {
        const { metrics, meta } = data;
        const shared = { studentId: scope.studentId };
        const hasNoResults = meta.data_warnings.some((w) => w.code === 'NO_RESULTS');
        return (
          <>
            {hasNoResults && (
              <EmptyState
                title="Chưa có kết quả học tập"
                description="Các chỉ số sẽ hiện khi có điểm đầu tiên."
              />
            )}
            <div className="overview-stats">
              <div className="overview-cards metric-grid">
                <OverviewMetric
                  title="GPA học kỳ"
                  metricKey="semester_gpa"
                  value={formatDecimal(metrics.semester_gpa.value)}
                  to={link('/m11/phan-tich')}
                  {...shared}
                />
                <OverviewMetric
                  title="GPA tích lũy"
                  metricKey="cumulative_gpa"
                  value={formatDecimal(metrics.cumulative_gpa.value)}
                  to={link('/m11/phan-tich')}
                  {...shared}
                />
                <OverviewMetric
                  title="Tín chỉ đạt"
                  metricKey="credits_passed"
                  value={formatCount(metrics.credits_passed.value)}
                  to={link('/m11/phan-tich')}
                  {...shared}
                />
                <OverviewMetric
                  title="Số môn chưa đạt"
                  metricKey="failed_course_count"
                  value={formatCount(metrics.failed_course_count.value)}
                  to={failedListLink(search, scope.semesterId)}
                  {...shared}
                />
              </div>
              <ChartPanel
                id="overview-credit-pie"
                title="Tín chỉ theo chương trình đào tạo"
                resource={credits}
                errorText="Không tải được biểu đồ tín chỉ"
              >
                {(body) => <CreditPie credits={body} />}
              </ChartPanel>
              <ChartPanel
                id="overview-gpa-bars"
                title="Điểm trung bình theo kỳ"
                resource={trend}
                errorText="Không tải được biểu đồ điểm trung bình"
              >
                {(body) => <GpaBars trend={body} />}
              </ChartPanel>
            </div>
          </>
        );
      }}
    </ResourceView>
  );
}

/** Hồ sơ của sinh viên đang xem: sinh viên là chính mình; cố vấn, quản trị là sinh viên đã chọn. */
function useViewedProfile(role, scope) {
  let path = null;
  if (role === 'student') {
    path = '/api/students/me';
  } else if (scope?.studentId) {
    path = `/api/students/${encodeURIComponent(scope.studentId)}`;
  }
  return useApiResource(path);
}

/** Dải hồ sơ: "Mã SV - Họ tên", "Khóa · Ngành", bộ chọn kỳ bên phải (D-306). */
function ProfileBand() {
  const { identity, role } = useAuth();
  const scope = useM11ScopeValue();
  const profile = useViewedProfile(role, scope);
  let title;
  let line = role === 'student' ? null : ROLE_LABELS[role];
  if (profile.status === 'ok') {
    const { student_code: code, full_name: name, cohort, program } = profile.data;
    title = `${code} - ${name}`;
    line = [cohort, program?.name].filter(Boolean).join(' · ');
  } else if (role === 'student') {
    title = identity.user.full_name;
  }
  return (
    <WelcomeCard
      name={identity.user.full_name}
      title={title}
      line={line}
      action={scope && <SemesterFilter scope={scope} id="overview-semester" />}
    />
  );
}

const SHORTCUTS = ['/m11/ket-qua', '/m11/phan-tich', '/m12/dinh-huong', '/m12/yeu-cau-ho-tro'];

export default function OverviewPage() {
  return (
    <>
      <h1 className="visually-hidden">Tổng quan</h1>
      <ProfileBand />
      <M11Page>{(scope) => <OverviewContent scope={scope} />}</M11Page>
      <ShortcutGrid paths={SHORTCUTS} />
    </>
  );
}
