import { useState } from 'react';
import { useNavigate } from 'react-router';
import { apiRequest } from '../../api/client';
import { useAuth } from '../auth/AuthContext';
import { Button, Card, StatusChip } from '../../components/ui';
import { formatCount, formatDecimal, withQuery } from './format';
import { DISCLAIMER, RULE_NAMES } from './labels';
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
      ['Ngưỡng Cần chú ý', `dưới ${formatDecimal(e.watch_below)}`],
      ['Ngưỡng Nguy cơ cao', `dưới ${formatDecimal(e.warning_below)}`],
    ];
  }
  if (outcome.rule_code === 'debt') {
    return [
      ['Giá trị thực tế', `${formatCount(e.debt_credits)} tín chỉ nợ`],
      ['Ngưỡng Cần chú ý', `từ ${formatCount(e.watch_from)} tín chỉ`],
      ['Ngưỡng Nguy cơ cao', `từ ${formatCount(e.warning_from)} tín chỉ`],
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

const PLAN_API = '/api/m12/improvement-plan';
const PLAN_PAGE = '/m11/canh-bao/ke-hoach';

/** Q107: đã có kế hoạch thì mở kế hoạch đó. Cố vấn chỉ xem. */
function ImprovementAction({ scope }) {
  const { role } = useAuth();
  const navigate = useNavigate();
  const resource = useApiResource(withQuery(PLAN_API, { student_id: scope.studentId }));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const planPage = withQuery(PLAN_PAGE, { student: scope.studentId });
  if (resource.status !== 'ok') {
    return null;
  }
  const { plan, active_rules: rules } = resource.data;
  if (plan) {
    return (
      <div>
        <Button variant="secondary" to={planPage}>
          Xem kế hoạch
        </Button>
      </div>
    );
  }
  if (role !== 'student') {
    return <p className="reference-line">Sinh viên chưa tạo kế hoạch cải thiện.</p>;
  }
  if (rules.length === 0) {
    return <p className="reference-line">Không có quy tắc nào cần lập kế hoạch cải thiện.</p>;
  }
  async function create() {
    setBusy(true);
    setError('');
    try {
      await apiRequest(PLAN_API, { method: 'POST', body: {} });
      navigate(planPage);
    } catch (cause) {
      setError(cause.message);
      setBusy(false);
    }
  }
  return (
    <div>
      <Button loading={busy} onClick={create}>
        Tạo kế hoạch cải thiện
      </Button>
      {error && (
        <p role="alert" className="status-error">
          {error}
        </p>
      )}
    </div>
  );
}

/** Khối "Cảnh báo học vụ" (GPA, nợ, khối lượng đăng ký) của trang Phân tích & Cảnh báo (D-310). */
export function RisksContent({ scope }) {
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
          <div className="rule-grid">
            {data.outcomes.map((outcome) => (
              <RiskRuleCard key={outcome.rule_code} outcome={outcome} />
            ))}
          </div>
          <div>
            <ReferenceLine
              semesterName={semesterName}
              computedAt={data.meta.computed_at}
              ruleVersion={data.meta.rule_version}
            />
            <DataWarnings warnings={data.meta.data_warnings} />
          </div>
          <ImprovementAction scope={scope} />
        </div>
      )}
    </ResourceView>
  );
}
