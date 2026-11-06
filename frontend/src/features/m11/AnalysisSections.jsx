import { useState } from 'react';
import {
  DataTable,
  Disclosure,
  EmptyState,
  FormField,
  ProgressBar,
  Select,
  StatusChip,
} from '../../components/ui';
import {
  courseCode,
  formatCount,
  formatDecimal,
  formatSignedCount,
  formatSignedDecimal,
  withQuery,
} from './format';
import useApiResource from './useApiResource';
import { ResourceView } from './ui';

function CourseLabel({ course }) {
  return (
    <>
      {courseCode(course.code)} – {course.name}
    </>
  );
}

function ProgressRow({ label, passed, total }) {
  const known = passed !== null && passed !== undefined;
  const percent = known && total > 0 ? Math.min(100, Math.round((passed / total) * 100)) : 0;
  return (
    <ProgressBar
      label={label}
      percent={percent}
      valueText={`${formatCount(passed)}/${formatCount(total)} tín chỉ`}
    />
  );
}

export function CreditProgress({ data }) {
  return (
    <>
      <p className="card-text">
        Đạt {formatCount(data.passed)} · Nợ {formatCount(data.debt)} · Đang học{' '}
        {formatCount(data.in_progress)} · Số môn chưa đạt {formatCount(data.failed_courses)}
      </p>
      <ProgressRow
        label="Bắt buộc"
        passed={data.required.passed_credits}
        total={data.required.total_credits}
      />
      {data.elective_groups.map((group) => (
        <div key={group.group_id}>
          <ProgressRow label={group.name} passed={group.passed_credits} total={group.min_credits} />
          {group.label && <p className="table-note">{group.label}</p>}
        </div>
      ))}
    </>
  );
}

export function CurriculumCheck({ data }) {
  return (
    <>
      <p className="card-text">
        Chương trình: {data.program.name} (khóa {data.program.effective_cohort})
      </p>
      <Disclosure summary={`Môn bắt buộc còn thiếu (${data.missing_required.length})`}>
        <ul>
          {data.missing_required.map((course) => (
            <li key={course.course_id}>
              <CourseLabel course={course} />
            </li>
          ))}
        </ul>
      </Disclosure>
      <Disclosure summary={`Nhóm tự chọn chưa đủ (${data.unmet_elective_groups.length})`}>
        <ul>
          {data.unmet_elective_groups.map((group) => (
            <li key={group.group_id}>
              {group.name}: thiếu {formatCount(group.missing_credits)} tín chỉ
            </li>
          ))}
        </ul>
      </Disclosure>
      <Disclosure summary={`Môn chưa đủ tiên quyết (${data.blocked_courses.length})`}>
        <ul>
          {data.blocked_courses.map((course) => (
            <li key={course.course_id}>
              <CourseLabel course={course} />. Cần đạt trước:{' '}
              {course.missing_prerequisites.map((item) => courseCode(item.code)).join(', ')}
            </li>
          ))}
        </ul>
      </Disclosure>
    </>
  );
}

export function StrengthsList({ data }) {
  return (
    <ul className="strength-list">
      {data.groups.map((group) => (
        <li key={group.group_id}>
          <div className="strength-list__head">
            <strong>{group.name}</strong>
            <StatusChip status={group.level} />
          </div>
          {group.level !== 'insufficient_data' && <p>GPA nhóm {formatDecimal(group.value)}</p>}
          {group.courses.length > 0 && (
            <p className="table-note">
              Môn làm bằng chứng: {group.courses.map((c) => courseCode(c.code)).join(', ')}
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}

function CompareTable({ data }) {
  const rows = [
    {
      name: 'GPA',
      first: formatDecimal(data.semester_a.gpa),
      second: formatDecimal(data.semester_b.gpa),
      delta: formatSignedDecimal(data.gpa_delta),
    },
    {
      name: 'Tín chỉ',
      first: data.semester_a.credits,
      second: data.semester_b.credits,
      delta: formatSignedCount(data.credit_delta),
    },
    {
      name: 'Số môn đạt',
      first: data.semester_a.passed_count,
      second: data.semester_b.passed_count,
      delta: formatSignedCount(data.passed_delta),
    },
    {
      name: 'Số môn chưa đạt',
      first: data.semester_a.failed_count,
      second: data.semester_b.failed_count,
      delta: formatSignedCount(data.failed_delta),
    },
  ];
  const columns = [
    { key: 'name', header: 'Chỉ số', rowHeader: true },
    { key: 'first', header: data.semester_a.name },
    { key: 'second', header: data.semester_b.name },
    { key: 'delta', header: 'Chênh lệch' },
  ];
  return (
    <DataTable
      columns={columns}
      rows={rows}
      rowKey={(row) => row.name}
      ariaLabel="So sánh hai kỳ"
    />
  );
}

export function SemesterCompare({ scope }) {
  const items = scope.semesters.data.items;
  const position = items.findIndex((item) => item.id === scope.semesterId);
  const [choice, setChoice] = useState({});
  const b = choice.b ?? scope.semesterId;
  const a = choice.a ?? items[Math.max(0, position - 1)]?.id;
  const resource = useApiResource(
    items.length >= 2 && a && b
      ? withQuery('/api/m11/compare', { student_id: scope.studentId, a, b })
      : null,
  );

  if (items.length < 2) {
    return <EmptyState compact heading="p" title="Chưa đủ 2 học kỳ để so sánh." />;
  }

  function select(id, label, value, side) {
    return (
      <FormField id={id} label={label}>
        <Select
          value={value}
          onChange={(event) => setChoice((old) => ({ ...old, [side]: event.target.value }))}
        >
          {items.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </Select>
      </FormField>
    );
  }

  return (
    <>
      <div className="filter-bar">
        {select('compare-a', 'Kỳ thứ nhất', a, 'a')}
        {select('compare-b', 'Kỳ thứ hai', b, 'b')}
      </div>
      <ResourceView
        compact
        resource={resource}
        loadingText="Đang so sánh..."
        errorText="Không so sánh được"
      >
        {(data) => (
          <>
            {data.semester_a.credits === 0 && data.semester_b.credits === 0 && (
              <p className="card-text">Cả hai kỳ này đều chưa có kết quả.</p>
            )}
            <CompareTable data={data} />
          </>
        )}
      </ResourceView>
    </>
  );
}
