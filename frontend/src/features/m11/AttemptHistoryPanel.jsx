import { courseCode, formatDecimal, withQuery } from './format';
import { ATTEMPT_STATUSES, GRADE_STATUSES } from './labels';
import useApiResource from './useApiResource';
import { LevelBadge, ResourceView, SidePanel } from './ui';

function statusOf(item) {
  if (item.status in ATTEMPT_STATUSES) {
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
                <LevelBadge level={statusOf(item)} levels={GRADE_STATUSES} />
                {item.is_effective && (
                  <span className="attempt-list__effective">Lần được tính</span>
                )}
              </li>
            ))}
          </ol>
        )}
      </ResourceView>
    </SidePanel>
  );
}
