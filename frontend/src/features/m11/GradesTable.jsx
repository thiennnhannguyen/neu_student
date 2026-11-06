import { AlertTriangle, RotateCcw } from 'lucide-react';
import { Button, DataTable, StatusChip, Tooltip } from '../../components/ui';
import { courseCode, formatCount, formatDecimal } from './format';

const isBlank = (key) => (row) => row[key] === null || row[key] === undefined;

function CourseNameCell({ row, onOpenHistory }) {
  return (
    <div className="cell-stack">
      <span>{row.name}</span>
      {row.has_retake && (
        <Button
          variant="secondary"
          size="sm"
          iconLeft={RotateCcw}
          aria-label={`Xem lịch sử học lại ${row.name} (${courseCode(row.code)})`}
          onClick={() => onOpenHistory(row)}
        >
          Học lại
        </Button>
      )}
      {!row.counts_gpa && <span className="table-note">Không tính GPA</span>}
      {row.via_course && (
        <span className="table-note">Qua môn {courseCode(row.via_course.code)}</span>
      )}
      {row.data_warnings.length > 0 && (
        <Tooltip
          label="Cảnh báo dữ liệu"
          icon={AlertTriangle}
          text={row.data_warnings.map((warning) => warning.message).join(' ')}
        />
      )}
    </div>
  );
}

/** Sắp xếp chỉ trong trang hiện tại, vì API không có tham số sắp xếp (D-178). */
export default function GradesTable({ rows, onOpenHistory }) {
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
      render: (row) => <CourseNameCell row={row} onOpenHistory={onOpenHistory} />,
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
      header: 'Điểm',
      sortable: true,
      isBlank: isBlank('score_10'),
      render: (row) => formatDecimal(row.score_10),
    },
    {
      key: 'letter',
      header: 'Chữ',
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
    />
  );
}
