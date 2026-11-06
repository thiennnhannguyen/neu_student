import { SearchBox, Select } from '../../components/ui';

/** Ô chọn sinh viên từ 768px trở lên. Dưới 768px dùng ScopeChip. */
export default function StudentPicker({ students }) {
  return (
    <div className="student-picker">
      {students.canSearchInline && (
        <SearchBox
          aria-label="Tìm sinh viên"
          placeholder="Tìm mã hoặc tên"
          value={students.keyword}
          onChange={(event) => students.setKeyword(event.target.value)}
        />
      )}
      <label htmlFor="student-picker">Sinh viên</label>
      <Select
        id="student-picker"
        value={students.selected}
        onChange={(event) => students.choose(event.target.value)}
      >
        <option value="">Chọn sinh viên</option>
        {students.selectedMissing && <option value={students.selected}>{students.selected}</option>}
        {students.items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.student_code} – {item.full_name}
          </option>
        ))}
      </Select>
    </div>
  );
}
