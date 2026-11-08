/**
 * Xem lại báo cáo tuần của một môn, chỉ đọc (CR-12, D-312). Mở từ cột "Báo cáo tuần" ở trang
 * Phân tích & Cảnh báo. Sinh viên xem của mình; cố vấn được phân công và quản trị xem của sinh viên
 * đã chọn, kèm cờ "không khớp LMS" (API không trả cờ này cho sinh viên).
 */
import { SidePanel } from '../../components/ui';
import { courseCode, formatCount, formatDay, withQuery } from '../m11/format';
import useApiResource from '../m11/useApiResource';
import { ResourceView } from '../m11/ui';
import { QUESTIONS, answerLabel } from './questions';

const MISMATCH_FIELDS = { attendance: 'attendance', assignment: 'assignment' };

/** Chữ của cột "Báo cáo tuần": đã nộp x/y, lần gần nhất, số báo cáo đang mở. */
export function weeklySummaryText(summary) {
  if (!summary) {
    return '—';
  }
  const parts = [`Đã nộp ${formatCount(summary.submitted)}/${formatCount(summary.expected)}`];
  if (summary.latest) {
    parts.push(
      `gần nhất tuần ${summary.latest.week_no} (${formatDay(summary.latest.submitted_on)})`,
    );
  }
  if (summary.open > 0) {
    parts.push(`${formatCount(summary.open)} đang mở`);
  }
  return parts.join(' · ');
}

function statusText(item) {
  if (item.status === 'submitted') {
    return `Đã nộp ngày ${formatDay(item.submitted_on)}`;
  }
  if (item.status === 'missed') {
    return 'Không nộp';
  }
  return `Đang mở, hạn hết ngày ${formatDay(item.due_on)}`;
}

function Answers({ item }) {
  return (
    <dl className="detail-list weekly-history__answers">
      {QUESTIONS.map((question, index) => {
        const flagged = item.mismatch?.[MISMATCH_FIELDS[question.name]] === true;
        return (
          <div key={question.name}>
            <dt>
              {index + 1}. {question.label}
            </dt>
            <dd>
              {answerLabel(question.name, item.answers[question.name])}
              {flagged && <span className="weekly-history__flag">Không khớp dữ liệu LMS</span>}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}

export default function WeeklyReportHistory({ studentId, course, onClose }) {
  const resource = useApiResource(
    withQuery('/api/weekly-reports', { student_id: studentId, course_id: course.id }),
  );
  return (
    <SidePanel
      wide
      title={`Báo cáo tuần ${courseCode(course.code)} – ${course.name}`}
      onClose={onClose}
    >
      <p className="reference-line">Chỉ xem, không sửa được báo cáo đã nộp.</p>
      <ResourceView
        resource={resource}
        loadingText="Đang tải báo cáo tuần..."
        errorText="Không tải được báo cáo tuần"
        isEmpty={(data) => data.items.length === 0}
        emptyText="Chưa có báo cáo tuần nào mở"
        compact
      >
        {(data) => (
          <ol className="weekly-history">
            {[...data.items].reverse().map((item) => (
              <li key={item.week.week_no} className="weekly-history__item">
                <h3>
                  Tuần {item.week.week_no} ({formatDay(item.week.start)}–{formatDay(item.week.end)})
                </h3>
                <p className={`weekly-history__status weekly-history__status--${item.status}`}>
                  {statusText(item)}
                </p>
                {item.answers && <Answers item={item} />}
              </li>
            ))}
          </ol>
        )}
      </ResourceView>
    </SidePanel>
  );
}
