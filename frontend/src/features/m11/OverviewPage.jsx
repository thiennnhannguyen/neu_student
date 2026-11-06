import { Link, useLocation } from 'react-router';
import { ROLE_LABELS } from '../../components/menu';
import ShortcutGrid from '../../components/ShortcutGrid';
import { MetricCard, Skeleton } from '../../components/ui';
import WelcomeCard from '../../components/WelcomeCard';
import { useAuth } from '../auth/AuthContext';
import { formatCount, formatDecimal, withQuery } from './format';
import { DISCLAIMER, RISK_LEVELS } from './labels';
import M11Page from './M11Page';
import MetricInfo from './MetricInfo';
import { carrySearch } from './scopeQuery';
import useApiResource from './useApiResource';
import { DataWarnings, LevelBadge, ReferenceLine, ResourceView } from './ui';

function OverviewMetric({ title, metricKey, value, detail, to, metric, semesterName, studentId }) {
  return (
    <div className="span-3">
      <MetricCard
        label={title}
        value={value}
        hint={detail}
        to={to}
        info={<MetricInfo metricKey={metricKey} label={title} studentId={studentId} />}
        footer={
          <ReferenceLine
            semesterName={semesterName}
            computedAt={metric.computed_at}
            ruleVersion={metric.rule_version}
          />
        }
      />
    </div>
  );
}

function OverviewSkeleton() {
  return (
    <>
      <p role="status" className="visually-hidden">
        Đang tải tổng quan...
      </p>
      <div className="grid-12">
        {[1, 2, 3, 4].map((key) => (
          <div key={key} className="span-3 metric-card metric-card--skeleton">
            <Skeleton width="60%" />
            <Skeleton width="40%" height={36} />
            <Skeleton />
          </div>
        ))}
      </div>
    </>
  );
}

function OverviewContent({ scope }) {
  const { search } = useLocation();
  const resource = useApiResource(withQuery('/api/m11/overview', scope.query));
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
        const semesterName = data.semester?.name;
        const hasNoResults = meta.data_warnings.some((w) => w.code === 'NO_RESULTS');
        const shared = { semesterName, studentId: scope.studentId };
        return (
          <>
            {hasNoResults && (
              <p className="card empty-state">
                Chưa có kết quả học tập. Các chỉ số sẽ hiện khi có điểm đầu tiên.
              </p>
            )}
            <Link to={link('/m11/canh-bao')} className="risk-strip">
              <span>Mức cảnh báo chung</span>
              <LevelBadge level={metrics.risk_level.value} levels={RISK_LEVELS} />
              <span className="risk-strip__note">{DISCLAIMER}</span>
            </Link>
            <div className="grid-12">
              <OverviewMetric
                title="GPA học kỳ"
                metricKey="semester_gpa"
                value={formatDecimal(metrics.semester_gpa.value)}
                to={link('/m11/phan-tich')}
                metric={metrics.semester_gpa}
                {...shared}
              />
              <OverviewMetric
                title="GPA tích lũy"
                metricKey="cumulative_gpa"
                value={formatDecimal(metrics.cumulative_gpa.value)}
                to={link('/m11/phan-tich')}
                metric={metrics.cumulative_gpa}
                {...shared}
              />
              <OverviewMetric
                title="Tín chỉ đạt"
                metricKey="credits_passed"
                value={formatCount(metrics.credits_passed.value)}
                detail={`Nợ ${formatCount(metrics.credits_debt.value)} · Đang học ${formatCount(
                  metrics.credits_in_progress.value,
                )}`}
                to={link('/m11/phan-tich')}
                metric={metrics.credits_passed}
                {...shared}
              />
              <OverviewMetric
                title="Số môn chưa đạt"
                metricKey="failed_course_count"
                value={formatCount(metrics.failed_course_count.value)}
                to={link('/m11/ket-qua')}
                metric={metrics.failed_course_count}
                {...shared}
              />
            </div>
            <DataWarnings warnings={meta.data_warnings} />
          </>
        );
      }}
    </ResourceView>
  );
}

function Welcome() {
  const { identity, role } = useAuth();
  const isStudent = role === 'student';
  const profile = useApiResource(isStudent ? '/api/students/me' : null);
  let line = ROLE_LABELS[role];
  if (isStudent && profile.status === 'ok') {
    const { cohort, program, current_semester: semester } = profile.data;
    line = [cohort, program.name, semester?.name].filter(Boolean).join(' · ');
  }
  return <WelcomeCard name={identity.user.full_name} line={line} />;
}

const SHORTCUTS = ['/m11/ket-qua', '/m11/phan-tich', '/m12/dinh-huong', '/m12/yeu-cau-ho-tro'];

export default function OverviewPage() {
  return (
    <>
      <Welcome />
      <M11Page title="Tổng quan" description="Số liệu học tập chính của kỳ đang chọn.">
        {(scope) => <OverviewContent scope={scope} />}
      </M11Page>
      <ShortcutGrid paths={SHORTCUTS} />
    </>
  );
}
