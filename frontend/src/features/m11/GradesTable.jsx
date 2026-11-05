import { courseCode, formatCount, formatDecimal } from './format';
import { GRADE_STATUSES } from './labels';
import { LevelBadge } from './ui';

function DataWarningLabel({ warnings, id }) {
  return (
    <span className="warning-tip">
      <button type="button" className="warning-tip__label" aria-describedby={id}>
        Cảnh báo dữ liệu
      </button>
      <span role="tooltip" id={id} className="warning-tip__text">
        {warnings.map((warning) => warning.message).join(' ')}
      </span>
    </span>
  );
}

/** Trên thẻ di động, ô không có giá trị được ẩn để thẻ gọn. Trên bảng vẫn hiện gạch. */
function cellClass(value) {
  return value === null || value === undefined ? 'grades-table__blank' : undefined;
}

/** Dưới 768px, CSS biến mỗi dòng thành thẻ và lấy nhãn từ data-label. */
export default function GradesTable({ rows, onOpenHistory }) {
  return (
    // Vùng cuộn ngang phải nhận được focus để dùng bằng bàn phím.
    // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex
    <div className="grades-scroll" role="region" aria-label="Bảng điểm" tabIndex={0}>
      <table className="grades-table">
        <thead>
          <tr>
            <th scope="col">Mã môn</th>
            <th scope="col">Tên môn</th>
            <th scope="col">Tín chỉ</th>
            <th scope="col">Học kỳ</th>
            <th scope="col">Điểm</th>
            <th scope="col">Chữ</th>
            <th scope="col">Hệ 4</th>
            <th scope="col">Trạng thái</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.course_id}>
              <td data-label="Mã môn">{courseCode(row.code)}</td>
              <td data-label="Tên môn">
                <span>{row.name}</span>
                {row.has_retake && (
                  <button
                    type="button"
                    className="retake-button"
                    aria-label={`Xem lịch sử học lại ${row.name} (${courseCode(row.code)})`}
                    onClick={() => onOpenHistory(row)}
                  >
                    <span aria-hidden="true">↻</span> Học lại
                  </button>
                )}
                {!row.counts_gpa && <span className="grades-table__note">Không tính GPA</span>}
                {row.via_course && (
                  <span className="grades-table__note">
                    Qua môn {courseCode(row.via_course.code)}
                  </span>
                )}
                {row.data_warnings.length > 0 && (
                  <DataWarningLabel warnings={row.data_warnings} id={`warning-${row.course_id}`} />
                )}
              </td>
              <td data-label="Tín chỉ">{formatCount(row.credits)}</td>
              <td data-label="Học kỳ" className={cellClass(row.semester)}>
                {row.semester?.name ?? '—'}
              </td>
              <td data-label="Điểm" className={cellClass(row.score_10)}>
                {formatDecimal(row.score_10)}
              </td>
              <td data-label="Chữ" className={cellClass(row.letter)}>
                {row.letter ?? '—'}
              </td>
              <td data-label="Hệ 4" className={cellClass(row.grade_4)}>
                {formatDecimal(row.grade_4)}
              </td>
              <td data-label="Trạng thái">
                <LevelBadge level={row.status} levels={GRADE_STATUSES} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
