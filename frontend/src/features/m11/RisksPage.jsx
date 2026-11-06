import { Button, Card, StatusChip } from '../../components/ui';
import { formatCount, formatDecimal, withQuery } from './format';
import { DISCLAIMER, RULE_NAMES } from './labels';
import M11Page from './M11Page';
import MetricInfo from './MetricInfo';
import useApiResource from './useApiResource';
import { DataWarnings, ReferenceLine, ResourceView } from './ui';

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
    <Card
      as="article"
      title={RULE_NAMES[outcome.rule_code] ?? outcome.rule_code}
      actions={<StatusChip status={outcome.level} />}
      footer={
        <p className="reference-line">
          Phiên bản quy chế: {outcome.rule_version ?? 'Không xác định'}
        </p>
      }
    >
      <p className="card-text">{outcome.reason}</p>
      {hasEvidence && (
        <dl className="detail-list">
          {evidenceRows(outcome).map(([name, value]) => (
            <div key={name}>
              <dt>{name}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      )}
    </Card>
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
        <div className="stack">
          <Card
            title="Mức chung"
            actions={
              <MetricInfo metricKey="risk_level" label="Mức cảnh báo" studentId={scope.studentId} />
            }
          >
            <StatusChip status={data.overall} />
            <p className="card-note">{data.disclaimer ?? DISCLAIMER}</p>
          </Card>
          {data.outcomes.map((outcome) => (
            <RiskRuleCard key={outcome.rule_code} outcome={outcome} />
          ))}
          <div>
            <ReferenceLine
              semesterName={semesterName}
              computedAt={data.meta.computed_at}
              ruleVersion={data.meta.rule_version}
            />
            <DataWarnings warnings={data.meta.data_warnings} />
          </div>
          <div>
            <Button disabled>Tạo kế hoạch cải thiện</Button>
            <p className="reference-line">Có ở giai đoạn sau</p>
          </div>
        </div>
      )}
    </ResourceView>
  );
}

export default function RisksPage() {
  return (
    <M11Page title="Cảnh báo" description="Mức cảnh báo và căn cứ của từng quy tắc.">
      {(scope) => <RisksContent scope={scope} />}
    </M11Page>
  );
}
