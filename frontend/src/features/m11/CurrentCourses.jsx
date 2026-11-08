import { useState } from 'react';
import { Button, DataTable, EmptyState } from '../../components/ui';
import WeeklyReportHistory, { weeklySummaryText } from '../weeklyReport/WeeklyReportHistory';
import {
  courseCode,
  formatCount,
  formatDay,
  formatDecimal,
  weekdayName,
  withQuery,
} from './format';
import useApiResource from './useApiResource';
import { ResourceView } from './ui';

/** Tuần của môn tính theo lịch học của môn (D-309), không theo ngày đầu học kỳ. */
function weekText(latest) {
  const { week } = latest;
  return `Tuần ${week.week_no} (${formatDay(week.start)}–${formatDay(week.end)})`;
}

function absenceText(summary) {
  const excused = summary.excused > 0 ? `, ${formatCount(summary.excused)} có phép` : '';
  return `${formatCount(summary.absent + summary.excused)}/${formatCount(summary.sessions_held)} buổi${excused}`;
}

function assignmentText(summary) {
  const parts = [
    `${formatCount(summary.submitted)}/${formatCount(summary.assignments_total)} đã nộp`,
  ];
  if (summary.overdue > 0) {
    parts.push(`${formatCount(summary.overdue)} quá hạn`);
  }
  if (summary.late > 0) {
    parts.push(`${formatCount(summary.late)} nộp muộn`);
  }
  return parts.join(' · ');
}

const NO_DATA = 'Chưa có dữ liệu LMS';

const LMS_COLUMNS = [
  { key: 'code', header: 'Mã môn', render: (row) => courseCode(row.course.code) },
  { key: 'name', header: 'Tên môn', rowHeader: true, render: (row) => row.course.name },
  {
    key: 'schedule',
    header: 'Lịch học',
    render: (row) => (row.schedule ? weekdayName(row.schedule.weekday) : 'Chưa có lịch'),
  },
  {
    key: 'week',
    header: 'Dữ liệu tới',
    render: (row) => (row.latest ? weekText(row.latest) : NO_DATA),
  },
  {
    key: 'absent',
    header: 'Vắng',
    render: (row) => (row.latest ? absenceText(row.latest.summary) : '—'),
  },
  {
    key: 'assignments',
    header: 'Bài tập',
    render: (row) => (row.latest ? assignmentText(row.latest.summary) : '—'),
  },
  {
    key: 'average',
    header: 'Điểm TB bài tập',
    render: (row) => formatDecimal(row.latest?.summary.assignment_average),
  },
  {
    key: 'tests',
    header: 'Điểm kiểm tra',
    render: (row) => formatDecimal(row.latest?.summary.assessment_average),
  },
];

/** D-312: cột "Báo cáo tuần" – đã nộp x/y, lần gần nhất; "Xem" mở bản chỉ đọc. */
function weeklyColumn(onOpen) {
  return {
    key: 'weekly',
    header: 'Báo cáo tuần',
    render: (row) => (
      <span className="weekly-cell">
        <span>{weeklySummaryText(row.weekly_reports)}</span>
        {row.weekly_reports && row.weekly_reports.submitted + row.weekly_reports.missed > 0 && (
          <Button
            variant="ghost"
            size="sm"
            aria-label={`Xem báo cáo tuần môn ${courseCode(row.course.code)}`}
            onClick={() => onOpen(row.course)}
          >
            Xem
          </Button>
        )}
      </span>
    ),
  };
}

/** Các môn đang học kỳ hiện tại kèm bản LMS mới nhất. Chưa có dự đoán điểm (CR-13). */
export default function CurrentCourses({ scope }) {
  const resource = useApiResource(
    withQuery('/api/m11/current-courses', { student_id: scope.studentId }),
  );
  const [opened, setOpened] = useState(null);
  const columns = [...LMS_COLUMNS, weeklyColumn(setOpened)];
  const currentId = scope.semesters.data.current_id;
  return (
    <section className="current-courses" aria-labelledby="current-courses-title">
      <h2 id="current-courses-title" className="section-heading">
        Môn đang học kỳ này
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
                <DataTable
                  caption="Môn đang học và dữ liệu LMS mới nhất"
                  columns={columns}
                  rows={data.items}
                  rowKey={(row) => row.course.id}
                />
                <p className="reference-line">
                  Số liệu lấy từ LMS, tính tới ngày cập nhật của từng môn; tuần tính theo lịch học
                  của môn. Báo cáo tuần: số đã nộp trên số báo cáo đã hết hạn hoặc đã nộp. Ngày hệ
                  thống: {formatDay(data.today)}.
                </p>
                {opened && (
                  <WeeklyReportHistory
                    studentId={scope.studentId}
                    course={opened}
                    onClose={() => setOpened(null)}
                  />
                )}
              </>
            )
          }
        </ResourceView>
      )}
    </section>
  );
}
