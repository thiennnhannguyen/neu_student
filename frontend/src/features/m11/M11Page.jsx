import { EmptyState, PageHeader } from '../../components/ui';
import { useM11ScopeValue } from './M11ScopeContext';
import SemesterFilter from './SemesterFilter';
import { ResourceView } from './ui';

/**
 * Khung chung của các trang M11. Chưa chọn sinh viên thì chỉ hiện hướng dẫn, không gọi API.
 * title rỗng: trang tự lo tiêu đề (Tổng quan), khung chỉ còn hàng chọn kỳ.
 */
export default function M11Page({ title, description, children }) {
  const scope = useM11ScopeValue();
  const filter = <SemesterFilter scope={scope} />;
  return (
    <section className="m11-page">
      {title ? (
        <PageHeader title={title} description={description} actions={filter} />
      ) : (
        <div className="m11-toolbar">{filter}</div>
      )}
      {scope.needsStudent ? (
        <EmptyState
          title="Chưa chọn sinh viên"
          description='Chọn sinh viên ở ô "Sinh viên" trên thanh trên cùng để xem dữ liệu. Trên điện thoại, bấm nút "Đang xem".'
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
