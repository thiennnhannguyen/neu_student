import SemesterFilter from './SemesterFilter';
import useM11Scope from './useM11Scope';
import { ResourceView } from './ui';

/** Khung chung của các trang M11. Chưa chọn sinh viên thì chỉ hiện hướng dẫn, không gọi API. */
export default function M11Page({ title, allowAll = false, children }) {
  const scope = useM11Scope({ allowAll });
  return (
    <section className="m11-page">
      <div className="m11-page__header">
        <h1>{title}</h1>
        {!scope.needsStudent && <SemesterFilter scope={scope} allowAll={allowAll} />}
      </div>
      {scope.needsStudent ? (
        <p className="card empty-state">
          Chọn sinh viên ở ô &quot;Sinh viên&quot; trên thanh trên cùng để xem dữ liệu.
        </p>
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
