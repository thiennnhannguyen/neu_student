import {
  CreditProgress,
  CurriculumCheck,
  SemesterCompare,
  StrengthsList,
} from './AnalysisSections';
import { withQuery } from './format';
import GpaTrendChart from './GpaTrendChart';
import M11Page from './M11Page';
import MetricInfo from './MetricInfo';
import useApiResource from './useApiResource';
import { ReferenceLine, ResourceView } from './ui';

function Section({ title, metricKey, resource, scope, loadingText, children }) {
  const semesterName = scope.semesters.data.items.find((i) => i.id === scope.semesterId)?.name;
  return (
    <section className="card card--spaced">
      <h2 className="section-title">
        {title}
        {metricKey && (
          <MetricInfo metricKey={metricKey} label={title} studentId={scope.studentId} />
        )}
      </h2>
      <ResourceView
        resource={resource}
        loadingText={loadingText}
        errorText={`Không tải được ${title.toLowerCase()}`}
      >
        {(data) => (
          <>
            {children(data)}
            <ReferenceLine
              semesterName={semesterName}
              computedAt={data.meta.computed_at}
              ruleVersion={data.meta.rule_version}
            />
          </>
        )}
      </ResourceView>
    </section>
  );
}

function AnalysisContent({ scope }) {
  const path = (name) => withQuery(`/api/m11/${name}`, scope.query);
  const trend = useApiResource(path('gpa-trend'));
  const credits = useApiResource(path('credits'));
  const curriculum = useApiResource(path('curriculum-check'));
  const strengths = useApiResource(path('strengths'));
  const shared = { scope };
  return (
    <>
      <Section
        title="Xu hướng GPA"
        metricKey="gpa_trend"
        resource={trend}
        loadingText="Đang tải xu hướng..."
        {...shared}
      >
        {(data) => <GpaTrendChart trend={data} />}
      </Section>
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
      <Section
        title="Điểm mạnh và điểm yếu"
        metricKey="group_strength"
        resource={strengths}
        loadingText="Đang tải điểm mạnh, điểm yếu..."
        {...shared}
      >
        {(data) => <StrengthsList data={data} />}
      </Section>
      <section className="card card--spaced">
        <h2>So sánh hai kỳ</h2>
        <SemesterCompare key={scope.semesterId} scope={scope} />
      </section>
    </>
  );
}

export default function AnalysisPage() {
  return <M11Page title="Phân tích">{(scope) => <AnalysisContent scope={scope} />}</M11Page>;
}
