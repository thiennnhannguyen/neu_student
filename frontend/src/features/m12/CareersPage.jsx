import { ArrowRight } from 'lucide-react';
import { Button, EmptyState, PageHeader } from '../../components/ui';
import { withQuery } from '../m11/format';
import useApiResource from '../m11/useApiResource';
import { ResourceView } from '../m11/ui';
import ChooseCareer from './ChooseCareer';
import PrimaryCareerCard from './PrimaryCareerCard';
import RelatedCareerCard from './RelatedCareerCard';
import useCareerStudent from './useCareerStudent';

export const PICK_STUDENT_HINT =
  'Chọn sinh viên ở ô "Sinh viên" trên thanh trên cùng để xem dữ liệu. Trên điện thoại, bấm nút "Đang xem".';

function Content({ student, data, reload }) {
  if (!data.primary) {
    return student.isStudent ? (
      <ChooseCareer onChanged={reload} />
    ) : (
      <EmptyState title="Sinh viên này chưa chọn nghề chính" />
    );
  }
  return (
    <>
      <PrimaryCareerCard primary={data.primary} disclaimer={data.disclaimer} link={student.link} />
      <div className="career-section-head">
        <h2>Nghề liên quan</h2>
        <Button variant="ghost" iconRight={ArrowRight} to={student.link('/m12/dinh-huong/tat-ca')}>
          Xem tất cả
        </Button>
      </div>
      <p className="career-section-note">Đây là gợi ý, không phải nghề cấp dưới của nghề chính.</p>
      <div className="career-grid">
        {data.related.map((item) => (
          <RelatedCareerCard
            key={item.career.id}
            item={item}
            link={student.link}
            disclaimer={data.disclaimer}
          />
        ))}
      </div>
      <p className="career-disclaimer">{data.disclaimer}.</p>
    </>
  );
}

export default function CareersPage() {
  const student = useCareerStudent();
  const resource = useApiResource(
    student.needsStudent ? null : withQuery('/api/m12/my-careers', student.query),
  );
  return (
    <section className="m12-page">
      <PageHeader title="Định hướng nghề" description="Nghề chính và các nghề liên quan." />
      {student.needsStudent ? (
        <EmptyState title="Chưa chọn sinh viên" description={PICK_STUDENT_HINT} />
      ) : (
        <ResourceView
          resource={resource}
          loadingText="Đang tải định hướng nghề..."
          errorText="Không tải được định hướng nghề"
        >
          {(data) => <Content student={student} data={data} reload={resource.retry} />}
        </ResourceView>
      )}
    </section>
  );
}
