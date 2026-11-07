import { Card } from '../../components/ui';
import {
  CreditProgress,
  CurriculumCheck,
  SemesterCompare,
  StrengthsList,
} from './AnalysisSections';
import { withQuery } from './format';
import GpaTrendChart, { gpaThresholds } from './GpaTrendChart';
import M11Page from './M11Page';
import MetricInfo from './MetricInfo';
import useApiResource from './useApiResource';
import { ReferenceLine, ResourceView } from './ui';

function Section({ title, metricKey, resource, scope, loadingText, className, children }) {
  return (
    <div className={className}>
      <Card
        title={title}
        actions={
          metricKey && (
            <MetricInfo metricKey={metricKey} label={title} studentId={scope.studentId} />
          )
        }
      >
        <ResourceView
          compact
          resource={resource}
          loadingText={loadingText}
          errorText={`Không tải được ${title.toLowerCase()}`}
        >
          {children}
        </ResourceView>
      </Card>
    </div>
  );
}

/** Cả trang chung một kỳ, một quy chế nên chỉ có 1 dòng; lấy từ phần đầu tiên đã tải được. */
function SharedReference({ scope, resources }) {
  const loaded = resources.find((resource) => resource.status === 'ok');
  if (!loaded) {
    return null;
  }
  return (
    <ReferenceLine
      semesterName={scope.semesters.data.items.find((i) => i.id === scope.semesterId)?.name}
      computedAt={loaded.data.meta.computed_at}
      ruleVersion={loaded.data.meta.rule_version}
    />
  );
}

function AnalysisContent({ scope }) {
  const path = (name) => withQuery(`/api/m11/${name}`, scope.query);
  const trend = useApiResource(path('gpa-trend'));
  const credits = useApiResource(path('credits'));
  const curriculum = useApiResource(path('curriculum-check'));
  const strengths = useApiResource(path('strengths'));
  const risks = useApiResource(path('risks'));
  const shared = { scope };
  return (
    <>
      <div className="grid-12">
        <Section
          title="Xu hướng GPA"
          metricKey="gpa_trend"
          resource={trend}
          loadingText="Đang tải xu hướng..."
          {...shared}
        >
          {(data) => (
            <GpaTrendChart
              trend={data}
              thresholds={risks.status === 'ok' ? gpaThresholds(risks.data.outcomes) : null}
            />
          )}
        </Section>
        <div className="span-7 stack">
          <Section
            title="Tiến độ tín chỉ"
            metricKey="credits_passed"
            resource={credits}
            loadingText="Đang tải tín chỉ..."
            {...shared}
          >
            {(data) => <CreditProgress data={data} />}
          </Section>
          <Section
            title="Đối chiếu chương trình đào tạo"
            resource={curriculum}
            loadingText="Đang tải chương trình..."
            {...shared}
          >
            {(data) => <CurriculumCheck data={data} />}
          </Section>
        </div>
        <Section
          title="Điểm mạnh và điểm yếu"
          metricKey="group_strength"
          resource={strengths}
          loadingText="Đang tải điểm mạnh, điểm yếu..."
          className="span-5"
          {...shared}
        >
          {(data) => <StrengthsList data={data} />}
        </Section>
        <div>
          <Card title="So sánh hai kỳ">
            <ResourceView
              compact
              resource={trend}
              loadingText="Đang so sánh..."
              errorText="Không so sánh được"
            >
              {(data) => <SemesterCompare key={scope.semesterId} scope={scope} trend={data} />}
            </ResourceView>
          </Card>
        </div>
      </div>
      <SharedReference scope={scope} resources={[trend, credits, curriculum, strengths]} />
    </>
  );
}

export default function AnalysisPage() {
  return (
    <M11Page
      title="Phân tích"
      description="Xu hướng GPA, tiến độ tín chỉ và đối chiếu chương trình."
    >
      {(scope) => <AnalysisContent scope={scope} />}
    </M11Page>
  );
}
