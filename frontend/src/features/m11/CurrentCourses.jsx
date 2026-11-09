import { ChevronRight } from 'lucide-react';
import { Link, useNavigate } from 'react-router';
import { EmptyState } from '../../components/ui';
import { courseCode, formatDay, withQuery } from './format';
import MetricInfo from './MetricInfo';
import { DISCLAIMER, LEVELS, PredictionCell, scoreText } from './prediction';
import useApiResource from './useApiResource';
import { ResourceView } from './ui';

/** Trang chi tiết môn, giữ ?student= cho cố vấn và quản trị. */
export function courseDetailPath(courseId, studentId) {
  return withQuery(`/m11/phan-tich/mon/${encodeURIComponent(courseId)}`, { student: studentId });
}

/** Phần đọc thêm cho trình đọc màn hình, nối sau chữ hiển thị (tên, mã) để nhãn chứa chữ thấy được. */
function rowSuffix(row) {
  const { prediction } = row;
  const level = ['high', 'watch'].includes(prediction.level)
    ? ` · ${LEVELS[prediction.level].label}`
    : '';
  return `: điểm dự kiến ${scoreText(prediction)}${level}`;
}

/**
 * Bảng "Môn đang học kỳ này" (CR-13, D-314): 2 cột Môn học · Điểm dự kiến, cả dòng bấm được.
 * Thứ tự do backend xếp: Không đủ điều kiện dự thi → Nguy cơ cao → Cần chú ý → Ổn, cùng mức thì
 * điểm thấp trước. Ở 375px vẫn giữ 2 cột (không đổi thành thẻ như DataTable).
 */
function CoursesTable({ items, studentId }) {
  const navigate = useNavigate();
  // Chuột bấm chỗ nào trên dòng cũng mở trang chi tiết; bàn phím và trình đọc màn hình dùng liên kết
  // ở ô tên môn (dòng không nhận focus riêng).
  const openRow = (event, path) => {
    if (!event.target.closest('a')) {
      navigate(path);
    }
  };
  return (
    <table className="course-table">
      <caption className="visually-hidden">Môn đang học và điểm dự kiến</caption>
      <thead>
        <tr>
          <th scope="col">Môn học</th>
          <th scope="col" className="course-table__score">
            Điểm dự kiến
          </th>
        </tr>
      </thead>
      <tbody>
        {items.map((row) => (
          <tr
            key={row.course.id}
            className={`course-row course-row--${row.prediction.level}`}
            onClick={(event) => openRow(event, courseDetailPath(row.course.id, studentId))}
          >
            <th scope="row">
              <Link className="course-row__link" to={courseDetailPath(row.course.id, studentId)}>
                <span className="course-row__name">{row.course.name}</span>{' '}
                <span className="course-row__code">{courseCode(row.course.code)}</span>
                <span className="visually-hidden">{rowSuffix(row)}</span>
              </Link>
            </th>
            <td className="course-table__score">
              <span className="course-table__score-inner">
                <PredictionCell prediction={row.prediction} />
                <ChevronRight className="course-row__arrow" size={18} aria-hidden="true" />
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function CurrentCourses({ scope }) {
  const resource = useApiResource(
    withQuery('/api/m11/current-courses', { student_id: scope.studentId }),
  );
  const currentId = scope.semesters.data.current_id;
  return (
    <section className="current-courses" aria-labelledby="current-courses-title">
      <h2 id="current-courses-title" className="section-heading">
        Môn đang học kỳ này
        <MetricInfo
          metricKey="course_prediction"
          label="Điểm dự kiến của môn đang học"
          studentId={scope.studentId}
        />
      </h2>
      {scope.semesterId !== currentId ? (
        <p className="reference-line">
          Danh sách môn đang học chỉ có ở kỳ hiện tại. Chọn kỳ hiện tại để xem.
        </p>
      ) : (
        <ResourceView
          resource={resource}
          loadingText="Đang tải các môn đang học..."
          errorText="Không tải được các môn đang học"
          compact
        >
          {(data) =>
            data.items.length === 0 ? (
              <EmptyState
                compact
                heading="h3"
                title="Kỳ này chưa có môn đang học"
                description="Danh sách hiện khi sinh viên đăng ký môn ở kỳ hiện tại."
              />
            ) : (
              <>
                <CoursesTable items={data.items} studentId={scope.studentId} />
                <p className="reference-line">
                  {DISCLAIMER} Bấm vào môn để xem chi tiết. Ngày hệ thống: {formatDay(data.today)}.
                </p>
              </>
            )
          }
        </ResourceView>
      )}
    </section>
  );
}
