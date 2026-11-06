import { EmptyState, PageHeader } from '../../components/ui';
import SemesterFilter from './SemesterFilter';
import useM11Scope from './useM11Scope';
import { ResourceView } from './ui';

/** Khung chung của các trang M11. Chưa chọn sinh viên thì chỉ hiện hướng dẫn, không gọi API. */
export default function M11Page({ title, description, allowAll = false, children }) {
  const scope = useM11Scope({ allowAll });
  return (
    <section className="m11-page">
      <PageHeader
        title={title}
        description={description}
        actions={!scope.needsStudent && <SemesterFilter scope={scope} allowAll={allowAll} />}
      />
      {scope.needsStudent ? (
        <EmptyState
          title="Chưa chọn sinh viên"
          description='Chọn sinh viên ở ô "Sinh viên" trên thanh trên cùng để xem dữ liệu.'
        />
      ) : (
        <ResourceView
          resource={scope.semesters}
          loadingText="Đang tải học kỳ..."
          errorText="Không tải được dữ liệu của sinh viên này"
        >
          {() => children(scope)}
        </ResourceView>
      )}
    </section>
  );
}
