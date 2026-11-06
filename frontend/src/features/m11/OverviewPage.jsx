import { Link, useLocation } from 'react-router';
import { ROLE_LABELS } from '../../components/menu';
import ShortcutGrid from '../../components/ShortcutGrid';
import { Card, EmptyState, MetricCard, Skeleton, StatusChip } from '../../components/ui';
import WelcomeCard from '../../components/WelcomeCard';
import { useAuth } from '../auth/AuthContext';
import { formatCount, formatDecimal, gradedPoints, withQuery } from './format';
import { DISCLAIMER } from './labels';
import M11Page from './M11Page';
import { useM11ScopeValue } from './M11ScopeContext';
import MetricInfo from './MetricInfo';
import { carrySearch } from './scopeQuery';
import SemesterFilter from './SemesterFilter';
import useApiResource from './useApiResource';
import { DataWarnings, ReferenceLine, ResourceView } from './ui';

function OverviewMetric({ title, metricKey, value, detail, to, status, studentId }) {
  return (
    <div className="span-3">
      <MetricCard
        label={title}
        value={value}
        hint={detail}
        to={to}
        status={status}
        info={<MetricInfo metricKey={metricKey} label={title} studentId={studentId} />}
      />
    </div>
  );
}

const SHOWN_LEVELS = ['watch', 'warning'];

/** Mức của đúng quy tắc gắn với chỉ số; chỉ trả về khi cần chú ý. Chưa có dữ liệu thì không có mức. */
export function ruleStatus(risks, ruleCode) {
  if (risks.status !== 'ok') {
    return undefined;
  }
  const level = risks.data.outcomes.find((outcome) => outcome.rule_code === ruleCode)?.level;
  return SHOWN_LEVELS.includes(level) ? level : undefined;
}

/** Kỳ gần nhất có GPA, tính từ danh sách đã có ở /gpa-trend. Không đổi kỳ của các thẻ khác (Q80). */
function NoSemesterResult({ query }) {
  const trend = useApiResource(withQuery('/api/m11/gpa-trend', query));
  const point = trend.status === 'ok' ? gradedPoints(trend.data.points).at(-1) : null;
  return (
    <>
      <span>Kỳ này chưa có kết quả</span>
      {point && (
        <>
          {' · '}
          <span>
            Kỳ gần nhất có điểm ({point.semester_id}): {formatDecimal(point.value)}
          </span>
        </>
      )}
    </>
  );
}

function OverviewSkeleton() {
  return (
    <>
      <p role="status" className="visually-hidden">
        Đang tải tổng quan...
      </p>
      <div className="grid-12 metric-grid">
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
  const risks = useApiResource(withQuery('/api/m11/risks', scope.query));
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
            <Card as={Link} to={link('/m11/canh-bao')} className="risk-summary">
              <span className="risk-summary__label">Mức cảnh báo chung</span>
              <StatusChip status={metrics.risk_level.value} />
              <span className="risk-summary__note">{DISCLAIMER}</span>
            </Card>
            <div className="grid-12 metric-grid">
              <OverviewMetric
                title="GPA học kỳ"
                metricKey="semester_gpa"
                value={formatDecimal(metrics.semester_gpa.value)}
                detail={
                  metrics.semester_gpa.denominator === 0 ? (
                    <NoSemesterResult query={scope.query} />
                  ) : undefined
                }
                to={link('/m11/phan-tich')}
                {...shared}
              />
              <OverviewMetric
                title="GPA tích lũy"
                metricKey="cumulative_gpa"
                value={formatDecimal(metrics.cumulative_gpa.value)}
                status={ruleStatus(risks, 'gpa')}
                to={link('/m11/phan-tich')}
                {...shared}
              />
              <OverviewMetric
                title="Tín chỉ đạt"
                metricKey="credits_passed"
                value={formatCount(metrics.credits_passed.value)}
                status={ruleStatus(risks, 'debt')}
                detail={`Nợ ${formatCount(metrics.credits_debt.value)} · Đang học ${formatCount(
                  metrics.credits_in_progress.value,
                )}`}
                to={link('/m11/phan-tich')}
                {...shared}
              />
              <OverviewMetric
                title="Số môn chưa đạt"
                metricKey="failed_course_count"
                value={formatCount(metrics.failed_course_count.value)}
                to={link('/m11/ket-qua')}
                {...shared}
              />
            </div>
            <ReferenceLine
              semesterName={data.semester?.name}
              computedAt={meta.computed_at}
              ruleVersion={meta.rule_version}
            />
            <DataWarnings warnings={meta.data_warnings} />
          </>
        );
      }}
    </ResourceView>
  );
}

function Welcome() {
  const { identity, role } = useAuth();
  const scope = useM11ScopeValue();
  const isStudent = role === 'student';
  const profile = useApiResource(isStudent ? '/api/students/me' : null);
  let line = ROLE_LABELS[role];
  if (isStudent && profile.status === 'ok') {
    const { cohort, program, current_semester: semester } = profile.data;
    line = [cohort, program.name, semester?.name].filter(Boolean).join(' · ');
  }
  return (
    <WelcomeCard
      name={identity.user.full_name}
      line={line}
      action={scope && <SemesterFilter scope={scope} />}
    />
  );
}

const SHORTCUTS = ['/m11/ket-qua', '/m11/phan-tich', '/m12/dinh-huong', '/m12/yeu-cau-ho-tro'];

export default function OverviewPage() {
  return (
    <>
      <h1 className="visually-hidden">Tổng quan</h1>
      <Welcome />
      <M11Page>{(scope) => <OverviewContent scope={scope} />}</M11Page>
      <ShortcutGrid paths={SHORTCUTS} />
    </>
  );
}
