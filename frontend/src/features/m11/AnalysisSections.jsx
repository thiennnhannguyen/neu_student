import { useState } from 'react';
import {
  courseCode,
  formatCount,
  formatDecimal,
  formatSignedCount,
  formatSignedDecimal,
  withQuery,
} from './format';
import { GROUP_LEVELS } from './labels';
import useApiResource from './useApiResource';
import { LevelBadge, ResourceView } from './ui';

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
    <div className="progress-row">
      <p>
        <span>{label}</span>
        <strong>
          {formatCount(passed)}/{formatCount(total)} tín chỉ
        </strong>
      </p>
      <div
        className="progress-row__track"
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
      >
        <div className="progress-row__fill" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

export function CreditProgress({ data }) {
  return (
    <>
      <p>
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
          {group.label && <p className="grades-table__note">{group.label}</p>}
        </div>
      ))}
    </>
  );
}

export function CurriculumCheck({ data }) {
  return (
    <>
      <p>
        Chương trình: {data.program.name} (khóa {data.program.effective_cohort})
      </p>
      <details className="course-details">
        <summary>Môn bắt buộc còn thiếu ({data.missing_required.length})</summary>
        <ul>
          {data.missing_required.map((course) => (
            <li key={course.course_id}>
              <CourseLabel course={course} />
            </li>
          ))}
        </ul>
      </details>
      <details className="course-details">
        <summary>Nhóm tự chọn chưa đủ ({data.unmet_elective_groups.length})</summary>
        <ul>
          {data.unmet_elective_groups.map((group) => (
            <li key={group.group_id}>
              {group.name}: thiếu {formatCount(group.missing_credits)} tín chỉ
            </li>
          ))}
        </ul>
      </details>
      <details className="course-details">
        <summary>Môn chưa đủ tiên quyết ({data.blocked_courses.length})</summary>
        <ul>
          {data.blocked_courses.map((course) => (
            <li key={course.course_id}>
              <CourseLabel course={course} />. Cần đạt trước:{' '}
              {course.missing_prerequisites.map((item) => courseCode(item.code)).join(', ')}
            </li>
          ))}
        </ul>
      </details>
    </>
  );
}

export function StrengthsList({ data }) {
  return (
    <ul className="strength-list">
      {data.groups.map((group) => (
        <li key={group.group_id}>
          <p className="strength-list__head">
            <strong>{group.name}</strong>
            <LevelBadge level={group.level} levels={GROUP_LEVELS} />
          </p>
          {group.level !== 'insufficient_data' && <p>GPA nhóm {formatDecimal(group.value)}</p>}
          {group.courses.length > 0 && (
            <p className="grades-table__note">
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
    [
      'GPA',
      formatDecimal(data.semester_a.gpa),
      formatDecimal(data.semester_b.gpa),
      formatSignedDecimal(data.gpa_delta),
    ],
    [
      'Tín chỉ',
      data.semester_a.credits,
      data.semester_b.credits,
      formatSignedCount(data.credit_delta),
    ],
    [
      'Số môn đạt',
      data.semester_a.passed_count,
      data.semester_b.passed_count,
      formatSignedCount(data.passed_delta),
    ],
    [
      'Số môn chưa đạt',
      data.semester_a.failed_count,
      data.semester_b.failed_count,
      formatSignedCount(data.failed_delta),
    ],
  ];
  return (
    // Vùng cuộn ngang phải nhận được focus để dùng bằng bàn phím.
    // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex
    <div className="grades-scroll" role="region" aria-label="So sánh hai kỳ" tabIndex={0}>
      <table className="compare-table">
        <thead>
          <tr>
            <th scope="col">Chỉ số</th>
            <th scope="col">{data.semester_a.name}</th>
            <th scope="col">{data.semester_b.name}</th>
            <th scope="col">Chênh lệch</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([name, first, second, delta]) => (
            <tr key={name}>
              <th scope="row">{name}</th>
              <td>{first}</td>
              <td>{second}</td>
              <td>{delta}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
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
    return <p className="empty-state">Chưa đủ 2 học kỳ để so sánh.</p>;
  }

  function select(id, label, value, side) {
    return (
      <div className="field">
        <label htmlFor={id}>{label}</label>
        <select
          id={id}
          value={value}
          onChange={(event) => setChoice((old) => ({ ...old, [side]: event.target.value }))}
        >
          {items.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
      </div>
    );
  }

  return (
    <>
      <div className="filter-form">
        {select('compare-a', 'Kỳ thứ nhất', a, 'a')}
        {select('compare-b', 'Kỳ thứ hai', b, 'b')}
      </div>
      <ResourceView
        resource={resource}
        loadingText="Đang so sánh..."
        errorText="Không so sánh được"
      >
        {(data) => (
          <>
            {data.semester_a.credits === 0 && data.semester_b.credits === 0 && (
              <p className="empty-state">Cả hai kỳ này đều chưa có kết quả.</p>
            )}
            <CompareTable data={data} />
          </>
        )}
      </ResourceView>
    </>
  );
}
