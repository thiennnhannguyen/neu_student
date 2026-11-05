import { Link, useLocation } from 'react-router';
import { formatCount, formatDecimal, withQuery } from './format';
import { DISCLAIMER, RISK_LEVELS } from './labels';
import M11Page from './M11Page';
import MetricInfo from './MetricInfo';
import { carrySearch } from './scopeQuery';
import useApiResource from './useApiResource';
import { DataWarnings, LevelBadge, ReferenceLine, ResourceView } from './ui';

function MetricCard({ title, metricKey, value, detail, to, metric, semesterName, studentId }) {
  return (
    <article className="metric-card">
      <div className="metric-card__head">
        <Link to={to} className="metric-card__link">
          {title}
        </Link>
        <MetricInfo metricKey={metricKey} label={title} studentId={studentId} />
      </div>
      <p className="metric-card__value">{value}</p>
      {detail && <p className="metric-card__detail">{detail}</p>}
      <ReferenceLine
        semesterName={semesterName}
        computedAt={metric.computed_at}
        ruleVersion={metric.rule_version}
      />
    </article>
  );
}

function OverviewContent({ scope }) {
  const { search } = useLocation();
  const resource = useApiResource(withQuery('/api/m11/overview', scope.query));
  const link = (path) => `${path}${carrySearch(search)}`;
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
            <div className="metric-grid">
              <MetricCard
                title="GPA học kỳ"
                metricKey="semester_gpa"
                value={formatDecimal(metrics.semester_gpa.value)}
                to={link('/m11/phan-tich')}
                metric={metrics.semester_gpa}
                {...shared}
              />
              <MetricCard
                title="GPA tích lũy"
                metricKey="cumulative_gpa"
                value={formatDecimal(metrics.cumulative_gpa.value)}
                to={link('/m11/phan-tich')}
                metric={metrics.cumulative_gpa}
                {...shared}
              />
              <MetricCard
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
              <MetricCard
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

export default function OverviewPage() {
  return <M11Page title="Tổng quan">{(scope) => <OverviewContent scope={scope} />}</M11Page>;
}
