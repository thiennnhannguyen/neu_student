import { Clock } from 'lucide-react';
import { DataTable, StatusChip } from '../../components/ui';
import AttemptHistory from './AttemptHistory';
import { courseCode, formatCount, formatDecimal } from './format';

const isBlank = (key) => (row) => row[key] === null || row[key] === undefined;

/** Dòng học lại trông như dòng thường; lịch sử các lần học mở ở cột "Chi tiết" (CR-06). */
function CourseNameCell({ row }) {
  return (
    <div className="cell-stack">
      <span>{row.name}</span>
      {row.retaking_semester && (
        <span className="table-note table-note--icon">
          <Clock size={14} aria-hidden="true" />
          Đang học lại {row.retaking_semester.name}
        </span>
      )}
      {!row.counts_gpa && <span className="table-note">Không tính GPA</span>}
      {row.via_course && (
        <span className="table-note">Qua môn {courseCode(row.via_course.code)}</span>
      )}
    </div>
  );
}

/**
 * Dòng "Tổng kết học kì" (CR-06): có ở mọi kỳ khi xem một kỳ; kỳ chưa có điểm thì để trống các ô.
 * Số lấy từ API, không tự tính.
 */
function summaryFooter(summary) {
  if (!summary) {
    return undefined;
  }
  if (summary.credits === 0) {
    return { label: 'Tổng kết học kì', cells: { credits: '', score_10: '', grade_4: '' } };
  }
  return {
    label: 'Tổng kết học kì',
    cells: {
      credits: formatCount(summary.credits),
      score_10: formatDecimal(summary.score_10),
      grade_4: formatDecimal(summary.grade_4),
    },
  };
}

/** Sắp xếp chỉ trong trang hiện tại, vì API không có tham số sắp xếp (D-178). */
export default function GradesTable({ rows, studentId, summary }) {
  const columns = [
    {
      key: 'code',
      header: 'Mã môn',
      sortable: true,
      render: (row) => courseCode(row.code),
    },
    {
      key: 'name',
      header: 'Tên môn',
      sortable: true,
      render: (row) => <CourseNameCell row={row} />,
    },
    {
      key: 'credits',
      header: 'Tín chỉ',
      sortable: true,
      render: (row) => formatCount(row.credits),
    },
    {
      key: 'semester',
      header: 'Học kỳ',
      sortable: true,
      sortValue: (row) => row.semester?.order,
      isBlank: isBlank('semester'),
      render: (row) => row.semester?.name ?? '—',
    },
    {
      key: 'score_10',
      header: 'Điểm hệ 10',
      sortable: true,
      isBlank: isBlank('score_10'),
      render: (row) => formatDecimal(row.score_10),
    },
    {
      key: 'letter',
      header: 'Điểm chữ',
      isBlank: isBlank('letter'),
      render: (row) => row.letter ?? '—',
    },
    {
      key: 'grade_4',
      header: 'Hệ 4',
      sortable: true,
      isBlank: isBlank('grade_4'),
      render: (row) => formatDecimal(row.grade_4),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (row) => <StatusChip status={row.status} />,
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={rows}
      rowKey={(row) => row.course_id}
      ariaLabel="Bảng điểm"
      className="grades-table"
      detail={{
        header: 'Chi tiết',
        label: (row) => `Chi tiết ${row.name} (${courseCode(row.code)})`,
        render: (row) => <AttemptHistory row={row} studentId={studentId} />,
      }}
      footer={summaryFooter(summary)}
    />
  );
}
