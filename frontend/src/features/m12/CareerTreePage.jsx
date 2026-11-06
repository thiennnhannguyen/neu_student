import { useState } from 'react';
import { useParams } from 'react-router';
import { Badge, Card, EmptyState, PageHeader } from '../../components/ui';
import { withQuery } from '../m11/format';
import useApiResource from '../m11/useApiResource';
import { DataWarnings, ResourceView } from '../m11/ui';
import { PICK_STUDENT_HINT } from './CareersPage';
import CareerTree from './CareerTree';
import ProgressBars from './ProgressBars';
import RequirementPanel from './RequirementPanel';
import SetGoalButton from './SetGoalButton';
import useCareerStudent from './useCareerStudent';

function Tree({ student, data, reload }) {
  const [selected, setSelected] = useState(null);
  return (
    <>
      <Card className="career-tree-summary">
        <div className="career-tree-summary__head">
          <p className="related-career__field">{data.career.field}</p>
          {data.is_primary && <Badge tone="info">Nghề chính</Badge>}
          {student.isStudent && !data.is_primary && (
            <SetGoalButton career={data.career} onChanged={reload} />
          )}
        </div>
        <ProgressBars item={data} disclaimer={data.disclaimer} withInfo />
      </Card>
      <DataWarnings warnings={data.data_warnings} />
      <h2 className="career-section-title">Nhóm năng lực</h2>
      <CareerTree
        label={`Cây nghề ${data.career.name}`}
        nodes={data.nodes}
        onSelect={setSelected}
      />
      <p className="career-disclaimer">{data.disclaimer}.</p>
      {selected && (
        <RequirementPanel child={selected} link={student.link} onClose={() => setSelected(null)} />
      )}
    </>
  );
}

export default function CareerTreePage() {
  const { careerId } = useParams();
  const student = useCareerStudent();
  const resource = useApiResource(
    student.needsStudent ? null : withQuery(`/api/m12/progress/careers/${careerId}`, student.query),
  );
  const name = resource.status === 'ok' ? resource.data.career.name : 'Cây nghề';

  return (
    <section className="m12-page">
      <PageHeader title={name} description="Trạng thái luôn tính từ kết quả học tập hiện tại." />
      {student.needsStudent ? (
        <EmptyState title="Chưa chọn sinh viên" description={PICK_STUDENT_HINT} />
      ) : (
        <ResourceView
          resource={resource}
          loadingText="Đang tải cây nghề..."
          errorText="Không tải được cây nghề"
        >
          {(data) => <Tree key={careerId} student={student} data={data} reload={resource.retry} />}
        </ResourceView>
      )}
    </section>
  );
}
