import { SlidersHorizontal } from 'lucide-react';
import { useState } from 'react';
import { BottomSheet, Button, SearchBox } from '../../components/ui';
import { useM11ScopeValue } from './M11ScopeContext';
import SemesterFilter from './SemesterFilter';
import { ALL_SEMESTERS } from './useM11Scope';

export function scopeChipText(students, scope) {
  const parts = [];
  if (students.enabled) {
    parts.push(students.selected ? students.selectedCode : 'Chưa chọn');
  }
  if (scope?.semesterId) {
    const name =
      scope.semesters?.status === 'ok'
        ? scope.semesters.data.items.find((item) => item.id === scope.semesterId)?.name
        : null;
    parts.push(scope.semesterId === ALL_SEMESTERS ? 'Tất cả' : (name ?? scope.semesterId));
  }
  return parts.join(' · ');
}

function StudentChoices({ students }) {
  const options = students.selectedMissing
    ? [{ id: students.selected, label: students.selected }]
    : [];
  for (const item of students.items) {
    options.push({ id: item.id, label: `${item.student_code} – ${item.full_name}` });
  }
  return (
    <>
      <div className="form-field">
        <label htmlFor="scope-search">Tìm sinh viên</label>
        <SearchBox
          id="scope-search"
          placeholder="Tìm mã hoặc tên"
          value={students.keyword}
          onChange={(event) => students.setKeyword(event.target.value)}
        />
      </div>
      {options.length > 0 ? (
        <div role="radiogroup" aria-label="Danh sách sinh viên" className="choice-list">
          {options.map((option) => (
            <label key={option.id} className="choice-list__item">
              <input
                type="radio"
                name="scope-student"
                checked={option.id === students.selected}
                onChange={() => students.choose(option.id)}
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
      ) : (
        <p className="scope-sheet__empty">Không có sinh viên phù hợp.</p>
      )}
    </>
  );
}

/** Dưới 768px, ô chọn sinh viên và bộ lọc kỳ gộp thành một nút; bấm mở tấm chọn ở đáy màn hình. */
export default function ScopeChip({ students }) {
  const scope = useM11ScopeValue();
  const [open, setOpen] = useState(false);

  if (!students.enabled && !scope) {
    return null;
  }

  const text = scopeChipText(students, scope);

  return (
    <>
      <button
        type="button"
        className="scope-chip"
        aria-label={`Đang xem: ${text}`}
        title={`Đang xem: ${text}`}
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
      >
        <SlidersHorizontal size={16} aria-hidden="true" />
        <span className="scope-chip__text">
          <span className="scope-chip__label">Đang xem:</span>
          <strong>{text}</strong>
        </span>
      </button>
      {open && (
        <BottomSheet
          title="Chọn phạm vi xem"
          onClose={() => setOpen(false)}
          footer={
            <Button className="scope-sheet__done" onClick={() => setOpen(false)}>
              Xong
            </Button>
          }
        >
          {students.enabled && <StudentChoices students={students} />}
          {scope && <SemesterFilter scope={scope} id="scope-semester" />}
        </BottomSheet>
      )}
    </>
  );
}
