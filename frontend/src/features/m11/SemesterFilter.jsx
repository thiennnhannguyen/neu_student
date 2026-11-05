import { ALL_SEMESTERS } from './useM11Scope';

export default function SemesterFilter({ scope, allowAll = false }) {
  if (scope.semesters.status !== 'ok') {
    return null;
  }
  return (
    <div className="field semester-filter">
      <label htmlFor="semester-filter">Học kỳ</label>
      <select
        id="semester-filter"
        value={scope.semesterId ?? ''}
        onChange={(event) => scope.setSemester(event.target.value)}
      >
        {allowAll && <option value={ALL_SEMESTERS}>Tất cả các kỳ</option>}
        {scope.semesters.data.items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.name}
            {item.is_current ? ' – hiện tại' : ''}
          </option>
        ))}
      </select>
    </div>
  );
}
