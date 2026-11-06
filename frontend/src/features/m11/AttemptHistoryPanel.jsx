import { Badge, SidePanel, StatusChip } from '../../components/ui';
import { courseCode, formatDecimal, withQuery } from './format';
import useApiResource from './useApiResource';
import { ResourceView } from './ui';

function statusOf(item) {
  if (item.status === 'in_progress' || item.status === 'exempt') {
    return item.status;
  }
  return item.passed ? 'done' : 'failed';
}

export default function AttemptHistoryPanel({ row, studentId, onClose }) {
  const resource = useApiResource(
    withQuery(`/api/m11/grades/${encodeURIComponent(row.course_id)}/attempts`, {
      student_id: studentId,
    }),
  );
  return (
    <SidePanel title={`Lịch sử học: ${courseCode(row.code)} ${row.name}`} onClose={onClose}>
      <ResourceView
        compact
        resource={resource}
        loadingText="Đang tải lịch sử..."
        errorText="Không tải được lịch sử"
        isEmpty={(data) => data.items.length === 0}
        emptyText="Chưa có lần học nào."
      >
        {(data) => (
          <ol className="attempt-list">
            {data.items.map((item) => (
              <li key={item.ordinal}>
                <p className="attempt-list__title">
                  Lần thứ {item.ordinal} · {item.semester.name}
                </p>
                <p>
                  Điểm {formatDecimal(item.score_10)} · Chữ {item.letter ?? '—'} · Hệ 4{' '}
                  {formatDecimal(item.grade_4)}
                </p>
                <div className="chip-row">
                  <StatusChip status={statusOf(item)} />
                  {item.is_effective && <Badge tone="info">Lần được tính</Badge>}
                </div>
              </li>
            ))}
          </ol>
        )}
      </ResourceView>
    </SidePanel>
  );
}
