import { formatCount, formatDecimal, withQuery } from './format';
import { DISCLAIMER, RISK_LEVELS, RULE_NAMES } from './labels';
import M11Page from './M11Page';
import MetricInfo from './MetricInfo';
import useApiResource from './useApiResource';
import { DataWarnings, LevelBadge, ReferenceLine, ResourceView } from './ui';

function evidenceRows(outcome) {
  const e = outcome.evidence;
  if (outcome.rule_code === 'gpa') {
    return [
      [
        'Giá trị thực tế',
        `${formatDecimal(e.value)} (${formatDecimal(e.numerator)}/${e.denominator})`,
      ],
      ['Ngưỡng chú ý', `dưới ${formatDecimal(e.watch_below)}`],
      ['Ngưỡng cảnh báo', `dưới ${formatDecimal(e.warning_below)}`],
    ];
  }
  if (outcome.rule_code === 'debt') {
    return [
      ['Giá trị thực tế', `${formatCount(e.debt_credits)} tín chỉ nợ`],
      ['Ngưỡng chú ý', `từ ${formatCount(e.watch_from)} tín chỉ`],
      ['Ngưỡng cảnh báo', `từ ${formatCount(e.warning_from)} tín chỉ`],
    ];
  }
  return [
    ['Giá trị thực tế', `${formatCount(e.registered_credits)} tín chỉ đăng ký`],
    ['Khoảng cho phép', `${formatCount(e.min_credits)}–${formatCount(e.max_credits)} tín chỉ`],
  ];
}

function RiskRuleCard({ outcome }) {
  const hasEvidence = Object.keys(outcome.evidence).length > 0;
  return (
    <article className="card card--spaced risk-card">
      <div className="risk-card__head">
        <h2>{RULE_NAMES[outcome.rule_code] ?? outcome.rule_code}</h2>
        <LevelBadge level={outcome.level} levels={RISK_LEVELS} />
      </div>
      <p>{outcome.reason}</p>
      {hasEvidence && (
        <dl className="profile-list">
          {evidenceRows(outcome).map(([name, value]) => (
            <div key={name}>
              <dt>{name}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      )}
      <p className="reference-line">
        Phiên bản quy chế: {outcome.rule_version ?? 'Không xác định'}
      </p>
    </article>
  );
}

function RisksContent({ scope }) {
  const resource = useApiResource(withQuery('/api/m11/risks', scope.query));
  const semesterName = scope.semesters.data.items.find((i) => i.id === scope.semesterId)?.name;
  return (
    <ResourceView
      resource={resource}
      loadingText="Đang tải cảnh báo..."
      errorText="Không tải được cảnh báo"
    >
      {(data) => (
        <>
          <p className="risk-overall">
            <span className="section-title">
              Mức chung
              <MetricInfo metricKey="risk_level" label="Mức cảnh báo" studentId={scope.studentId} />
            </span>
            <LevelBadge level={data.overall} levels={RISK_LEVELS} />
          </p>
          <p className="disclaimer">{data.disclaimer ?? DISCLAIMER}</p>
          {data.outcomes.map((outcome) => (
            <RiskRuleCard key={outcome.rule_code} outcome={outcome} />
          ))}
          <ReferenceLine
            semesterName={semesterName}
            computedAt={data.meta.computed_at}
            ruleVersion={data.meta.rule_version}
          />
          <DataWarnings warnings={data.meta.data_warnings} />
          <div className="plan-action">
            <button type="button" className="button" disabled>
              Tạo kế hoạch cải thiện
            </button>
            <p className="reference-line">Có ở giai đoạn sau</p>
          </div>
        </>
      )}
    </ResourceView>
  );
}

export default function RisksPage() {
  return <M11Page title="Cảnh báo">{(scope) => <RisksContent scope={scope} />}</M11Page>;
}
