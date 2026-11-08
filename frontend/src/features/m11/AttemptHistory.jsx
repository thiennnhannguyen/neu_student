import { STATUS_CHIPS } from '../../components/ui/StatusChip';
import { courseCode, withQuery } from './format';
import useApiResource from './useApiResource';
import { ResourceView } from './ui';

const MIN_ATTEMPT_COLUMNS = 3;
const FailedIcon = STATUS_CHIPS.failed.icon;

/** "10.00" → "10", "8.50" → "8,5", "7.25" → "7,25". Không có thì để trống như bảng điểm của trường. */
export function formatScore(value) {
  if (value === null || value === undefined) {
    return '';
  }
  const text = String(value);
  const trimmed = text.includes('.') ? text.replace(/0+$/, '').replace(/\.$/, '') : text;
  return trimmed.replace('.', ',');
}

function AttemptHeader({ index, attempt }) {
  return (
    <th scope="col">
      Điểm lần {index + 1}
      {attempt && (
        <span className="component-table__semester">
          {attempt.semester.name}
          {attempt.status === 'in_progress' && ' · đang học'}
          {attempt.passed === false && (
            <>
              {' · '}
              {/* D-304: icon ✗ của trạng thái "Chưa đạt" (CR-04) kèm chữ, lấy màu chữ của đầu cột. */}
              <span className="component-table__failed">
                <FailedIcon size={12} aria-hidden="true" />
                Chưa đạt
              </span>
            </>
          )}
          {attempt.is_effective && ' · Lần được tính'}
        </span>
      )}
    </th>
  );
}

function ComponentTable({ data }) {
  const count = Math.max(MIN_ATTEMPT_COLUMNS, data.items.length);
  const columns = Array.from({ length: count }, (_, index) => data.items[index] ?? null);
  return (
    <div
      className="component-table-wrap"
      role="region"
      aria-label="Bảng điểm thành phần"
      // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- cuộn ngang được bằng bàn phím
      tabIndex={0}
    >
      <table className="component-table">
        <thead>
          <tr>
            <th scope="col">STT</th>
            <th scope="col">Tên thành phần</th>
            <th scope="col">Trọng số</th>
            {columns.map((attempt, index) => (
              <AttemptHeader key={index} index={index} attempt={attempt} />
            ))}
          </tr>
        </thead>
        <tbody>
          {data.components.map((component, row) => (
            <tr key={component.key}>
              <td>{row + 1}</td>
              <td>{component.name}</td>
              <td>{component.weight}%</td>
              {columns.map((attempt, index) => (
                <td key={index}>{formatScore(attempt?.component_scores?.[component.key])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** "Chi tiết học phần" mở ngay dưới dòng (CR-06): điểm thành phần 10/40/50 theo từng lần học. */
export default function AttemptHistory({ row, studentId }) {
  const resource = useApiResource(
    withQuery(`/api/m11/grades/${encodeURIComponent(row.course_id)}/attempts`, {
      student_id: studentId,
    }),
  );
  const title = `Chi tiết học phần: ${courseCode(row.code)} - ${row.name}`;
  return (
    <section className="attempt-history" aria-label={title}>
      <p className="attempt-history__title">{title}</p>
      <ResourceView
        compact
        resource={resource}
        loadingText="Đang tải chi tiết..."
        errorText="Không tải được chi tiết học phần"
        isEmpty={(data) => data.items.length === 0}
        emptyText="Chưa có lần học nào."
      >
        {(data) => <ComponentTable data={data} />}
      </ResourceView>
    </section>
  );
}
