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
  gradedPoints,
  NO_VALUE,
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

const LEVEL_ORDER = { weak: 0, strong: 1, normal: 2 };

function GroupItem({ group }) {
  return (
    <li>
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
  );
}

/** Điểm yếu lên đầu để dễ thấy; nhóm chưa đủ dữ liệu gộp vào một khối thu gọn ở cuối. */
export function StrengthsList({ data }) {
  const unknown = data.groups.filter((group) => group.level === 'insufficient_data');
  const known = data.groups
    .filter((group) => group.level !== 'insufficient_data')
    .toSorted((first, second) => LEVEL_ORDER[first.level] - LEVEL_ORDER[second.level]);
  return (
    <>
      {known.length > 0 && (
        <ul className="strength-list">
          {known.map((group) => (
            <GroupItem key={group.group_id} group={group} />
          ))}
        </ul>
      )}
      {unknown.length > 0 && (
        <Disclosure summary={`Chưa đủ dữ liệu (${unknown.length})`}>
          <ul className="strength-list">
            {unknown.map((group) => (
              <GroupItem key={group.group_id} group={group} />
            ))}
          </ul>
        </Disclosure>
      )}
    </>
  );
}

const hasNoResult = (side) => side.gpa === null && side.credits === 0;

function CompareTable({ data }) {
  const { semester_a: first, semester_b: second } = data;
  const anyEmpty = hasNoResult(first) || hasNoResult(second);
  const count = (side, value) => (hasNoResult(side) ? NO_VALUE : value);
  const delta = (value) => (anyEmpty ? NO_VALUE : formatSignedCount(value));
  const rows = [
    {
      name: 'GPA',
      first: formatDecimal(first.gpa),
      second: formatDecimal(second.gpa),
      delta: formatSignedDecimal(data.gpa_delta),
    },
    {
      name: 'Tín chỉ',
      first: count(first, first.credits),
      second: count(second, second.credits),
      delta: delta(data.credit_delta),
    },
    {
      name: 'Số môn đạt',
      first: count(first, first.passed_count),
      second: count(second, second.passed_count),
      delta: delta(data.passed_delta),
    },
    {
      name: 'Số môn chưa đạt',
      first: count(first, first.failed_count),
      second: count(second, second.failed_count),
      delta: delta(data.failed_delta),
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

/** Mặc định là 2 kỳ gần nhất có điểm, lấy từ /gpa-trend; kỳ thứ nhất là kỳ cũ hơn. */
export function SemesterCompare({ scope, trend }) {
  const items = scope.semesters.data.items;
  const graded = gradedPoints(trend.points).map((point) => point.semester_id);
  const [choice, setChoice] = useState({});
  const a = choice.a ?? graded.at(-2);
  const b = choice.b ?? graded.at(-1);
  const resource = useApiResource(
    graded.length >= 2
      ? withQuery('/api/m11/compare', { student_id: scope.studentId, a, b })
      : null,
  );

  if (graded.length < 2) {
    return <EmptyState compact heading="p" title="Cần ít nhất 2 kỳ có kết quả để so sánh" />;
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
            {hasNoResult(data.semester_a) && hasNoResult(data.semester_b) && (
              <p className="card-text">Cả hai kỳ này đều chưa có kết quả.</p>
            )}
            <CompareTable data={data} />
          </>
        )}
      </ResourceView>
    </>
  );
}
