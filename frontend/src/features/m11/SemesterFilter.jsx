import { FormField, Select } from '../../components/ui';
import { ALL_SEMESTERS } from './useM11Scope';

export default function SemesterFilter({ scope, id = 'semester-filter' }) {
  if (scope.semesters.status !== 'ok') {
    return null;
  }
  return (
    <FormField id={id} label="Học kỳ" className="semester-filter">
      <Select
        value={scope.semesterId ?? ''}
        onChange={(event) => scope.setSemester(event.target.value)}
      >
        {scope.allowAll && <option value={ALL_SEMESTERS}>Tất cả các kỳ</option>}
        {scope.semesters.data.items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.name}
            {item.is_current ? ' – hiện tại' : ''}
          </option>
        ))}
      </Select>
    </FormField>
  );
}
