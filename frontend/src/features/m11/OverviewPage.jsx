import { Link, useLocation } from 'react-router';
import { ROLE_LABELS } from '../../components/menu';
import ShortcutGrid from '../../components/ShortcutGrid';
import { EmptyState, MetricCard, Skeleton, StatusChip } from '../../components/ui';
import WelcomeCard from '../../components/WelcomeCard';
import { useAuth } from '../auth/AuthContext';
import {
  formatCount,
  formatDate,
  formatDateTime,
  formatDecimal,
  gradedPoints,
  withQuery,
} from './format';
import { DISCLAIMER } from './labels';
import M11Page from './M11Page';
import { useM11ScopeValue } from './M11ScopeContext';
import MetricInfo from './MetricInfo';
import { carrySearch } from './scopeQuery';
import SemesterFilter from './SemesterFilter';
import useApiResource from './useApiResource';
import { DataWarnings, ResourceView } from './ui';

function OverviewMetric({ title, metricKey, value, hints, to, status, studentId }) {
  return (
    <div className="span-3">
      <MetricCard
        label={title}
        value={value}
        hint={hints}
        to={to}
        status={status}
        info={<MetricInfo metricKey={metricKey} label={title} studentId={studentId} />}
      />
    </div>
  );
}

const SHOWN_LEVELS = ['watch', 'warning'];
const SEVERITY = { warning: 2, watch: 1 };
const MAX_REASONS = 2;

/** Mức của đúng quy tắc gắn với chỉ số; chỉ trả về khi cần chú ý. Chưa có dữ liệu thì không có mức. */
export function ruleStatus(risks, ruleCode) {
  if (risks.status !== 'ok') {
    return undefined;
  }
  const level = risks.data.outcomes.find((outcome) => outcome.rule_code === ruleCode)?.level;
  return SHOWN_LEVELS.includes(level) ? level : undefined;
}

/** Tối đa 2 lý do ngắn từ API cảnh báo, mức cao trước. Mức "Ổn" thì không có lý do. */
export function riskReasons(risks) {
  if (risks.status !== 'ok') {
    return [];
  }
  return risks.data.outcomes
    .filter((outcome) => SHOWN_LEVELS.includes(outcome.level) && outcome.summary)
    .sort((a, b) => SEVERITY[b.level] - SEVERITY[a.level])
    .slice(0, MAX_REASONS);
}

/** Kỳ gần nhất có GPA, tính từ danh sách đã có ở /gpa-trend. Không đổi kỳ của các thẻ khác (Q80). */
function NoSemesterResult({ query }) {
  const trend = useApiResource(withQuery('/api/m11/gpa-trend', query));
  const point = trend.status === 'ok' ? gradedPoints(trend.data.points).at(-1) : null;
  return (
    <>
      <span className="q80-long">
        <span>Kỳ này chưa có kết quả</span>
        {point && (
          <>
            {' · '}
            <span>
              Kỳ gần nhất có điểm ({point.name}): {formatDecimal(point.value)}
            </span>
          </>
        )}
      </span>
      <span className="q80-short">
        Chưa có kết quả
        {point && ` · Gần nhất ${point.name}: ${formatDecimal(point.value)}`}
      </span>
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

/** Kỳ đang xem cạnh bộ chọn kỳ, trong thẻ chào (D-187); khác kỳ hiện tại thì có nhãn riêng. */
function ViewingBar({ scope }) {
  if (scope.semesters.status !== 'ok') {
    return null;
  }
  const { items, current_id: currentId } = scope.semesters.data;
  const viewing = items.find((item) => item.id === scope.semesterId);
  const current = items.find((item) => item.id === currentId);
  let tag = null;
  if (viewing && viewing.id === currentId) {
    tag = <span className="overview-viewing__current">(kỳ hiện tại)</span>;
  } else if (viewing && current && viewing.order < current.order) {
    tag = <span className="overview-viewing__past">Kỳ đã qua</span>;
  }
  return (
    <div className="overview-viewing">
      <p className="overview-viewing__label">
        Đang xem: <strong>{viewing?.name ?? '—'}</strong> {tag}
      </p>
      <SemesterFilter scope={scope} id="overview-semester" />
    </div>
  );
}

function RiskSummary({ level, risks, to }) {
  const reasons = level === 'normal' ? [] : riskReasons(risks);
  return (
    <Link to={to} className="risk-summary">
      <span className="risk-summary__head">
        <span className="risk-summary__label">Mức cảnh báo chung</span>
        <StatusChip status={level} />
      </span>
      {reasons.length > 0 && (
        <ul className="risk-summary__reasons">
          {reasons.map((reason) => (
            <li key={reason.rule_code}>
              <StatusChip status={reason.level} iconOnly />
              <span>{reason.summary}</span>
            </li>
          ))}
        </ul>
      )}
      <span className="risk-summary__note">{DISCLAIMER}</span>
    </Link>
  );
}

function OverviewTimes({ computedAt, gradesUpdatedAt, ruleVersion }) {
  return (
    <p className="reference-line overview-times">
      Tính lúc {formatDateTime(computedAt)} ·{' '}
      {gradesUpdatedAt
        ? `Điểm cập nhật lần cuối ${formatDate(gradesUpdatedAt)}`
        : 'Chưa ghi nhận thời điểm nhập điểm'}
      {ruleVersion ? ` · Quy chế ${ruleVersion}` : ''}
    </p>
  );
}

function scopeLine(metric, semesterName) {
  return metric.scope_label && semesterName ? `${metric.scope_label} ${semesterName}` : null;
}

/** Trang đích của thẻ "Số môn chưa đạt": đúng tập môn mà thẻ đếm, tính đến kỳ đang xem. */
export function failedListLink(search, semesterId) {
  const params = new URLSearchParams(carrySearch(search));
  if (semesterId) {
    params.set('semester', semesterId);
  }
  params.set('view', 'failed');
  return `/m11/ket-qua?${params.toString()}`;
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
        const name = data.semester?.name;
        const hasNoResults = meta.data_warnings.some((w) => w.code === 'NO_RESULTS');
        return (
          <>
            {hasNoResults && (
              <EmptyState
                title="Chưa có kết quả học tập"
                description="Các chỉ số sẽ hiện khi có điểm đầu tiên."
              />
            )}
            <div className="grid-12 metric-grid">
              <OverviewMetric
                title="GPA học kỳ"
                metricKey="semester_gpa"
                value={formatDecimal(metrics.semester_gpa.value)}
                hints={[
                  metrics.semester_gpa.denominator === 0 ? (
                    <NoSemesterResult key="q80" query={scope.query} />
                  ) : null,
                  scopeLine(metrics.semester_gpa, name),
                ]}
                to={link('/m11/phan-tich')}
                {...shared}
              />
              <OverviewMetric
                title="GPA tích lũy"
                metricKey="cumulative_gpa"
                value={formatDecimal(metrics.cumulative_gpa.value)}
                status={ruleStatus(risks, 'gpa')}
                hints={[scopeLine(metrics.cumulative_gpa, name)]}
                to={link('/m11/phan-tich')}
                {...shared}
              />
              <OverviewMetric
                title="Tín chỉ đạt"
                metricKey="credits_passed"
                value={formatCount(metrics.credits_passed.value)}
                hints={[
                  `Nợ ${formatCount(metrics.credits_debt.value)} · Đang học ${formatCount(
                    metrics.credits_in_progress.value,
                  )}`,
                  scopeLine(metrics.credits_passed, name),
                ]}
                to={link('/m11/phan-tich')}
                {...shared}
              />
              <OverviewMetric
                title="Số môn chưa đạt"
                metricKey="failed_course_count"
                value={formatCount(metrics.failed_course_count.value)}
                hints={[scopeLine(metrics.failed_course_count, name)]}
                to={failedListLink(search, scope.semesterId)}
                {...shared}
              />
            </div>
            <RiskSummary
              level={metrics.risk_level.value}
              risks={risks}
              to={link('/m11/canh-bao')}
            />
            <OverviewTimes
              computedAt={meta.computed_at}
              gradesUpdatedAt={data.grades_updated_at}
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
    line = [cohort, program.name, semester?.name && `Kỳ hiện tại: ${semester.name}`]
      .filter(Boolean)
      .join(' · ');
  }
  return (
    <WelcomeCard
      name={identity.user.full_name}
      line={line}
      action={scope && <ViewingBar scope={scope} />}
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
