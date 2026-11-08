import { useState } from 'react';
import { DataTable, StatusChip } from '../../components/ui';
import { courseChildren } from './CareerRoadmap';
import { chipStatus, NO_CODE, PRIORITIES, priorityLabel, typeLabel } from './labels';

const TYPES = [
  { id: 'required', label: 'BB' },
  { id: 'elective', label: 'TC' },
];

function FilterGroup({ label, options, selected, onSelect }) {
  return (
    <div className="career-filter__chips" role="group" aria-label={label}>
      {[{ id: '', label: 'Tất cả' }, ...options].map((option) => (
        <button
          key={option.id}
          type="button"
          className="career-filter__chip"
          aria-pressed={selected === option.id}
          onClick={() => onSelect(option.id)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

/** Bảng gọn các môn NEU của nghề, theo ngành của sinh viên. */
export default function CareerCourses({ nodes, onSelect }) {
  const [priority, setPriority] = useState('');
  const [type, setType] = useState('');
  const rows = nodes
    .flatMap(courseChildren)
    .filter((row) => !priority || row.priority === priority)
    .filter((row) => !type || row.requirement_type === type);
  const columns = [
    {
      key: 'title',
      header: 'Môn',
      rowHeader: true,
      render: (row) => (
        <button type="button" className="career-courses__link" onClick={() => onSelect(row)}>
          {row.title}
        </button>
      ),
    },
    {
      key: 'code',
      header: 'Mã',
      render: (row) => (row.not_in_program ? '—' : (row.code ?? NO_CODE)),
    },
    {
      key: 'requirement_type',
      header: 'BB/TC',
      render: (row) => typeLabel(row.requirement_type) ?? '—',
    },
    {
      key: 'planned_semester',
      header: 'Học kỳ',
      render: (row) => (row.planned_semester ? `HK ${row.planned_semester}` : '—'),
    },
    { key: 'priority', header: 'Mức ưu tiên', render: (row) => priorityLabel(row.priority) ?? '—' },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (row) => <StatusChip status={chipStatus(row.kind, row.status)} />,
    },
  ];
  return (
    <>
      <div className="career-courses__filters">
        <FilterGroup
          label="Lọc theo mức ưu tiên"
          options={PRIORITIES}
          selected={priority}
          onSelect={setPriority}
        />
        <FilterGroup label="Lọc theo BB/TC" options={TYPES} selected={type} onSelect={setType} />
      </div>
      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(row) => row.id}
        ariaLabel="Môn học NEU của nghề"
        caption="Môn học NEU của nghề"
      />
    </>
  );
}
