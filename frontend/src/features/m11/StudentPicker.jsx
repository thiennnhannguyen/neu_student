import { useState } from 'react';
import { useSearchParams } from 'react-router';
import { useAuth } from '../auth/AuthContext';
import { withQuery } from './format';
import useApiResource from './useApiResource';

const SOURCES = { advisor: '/api/advisor/students', admin: '/api/admin/students' };

export default function StudentPicker() {
  const { role } = useAuth();
  const [params, setParams] = useSearchParams();
  const [keyword, setKeyword] = useState('');
  const source = SOURCES[role];
  const resource = useApiResource(
    source ? withQuery(source, { q: keyword.trim(), page_size: 100 }) : null,
  );

  if (!source) {
    return null;
  }
  const selected = params.get('student') ?? '';
  const items = resource.status === 'ok' ? resource.data.items : [];
  const selectedMissing = selected && !items.some((item) => item.id === selected);

  function choose(event) {
    const value = event.target.value;
    setParams((current) => {
      const next = new URLSearchParams(current);
      next.delete('page');
      if (value) {
        next.set('student', value);
      } else {
        next.delete('student');
      }
      return next;
    });
  }

  return (
    <div className="student-picker">
      {role === 'admin' && (
        <input
          type="search"
          aria-label="Tìm sinh viên"
          placeholder="Tìm mã hoặc tên"
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
        />
      )}
      <label htmlFor="student-picker">Sinh viên</label>
      <select id="student-picker" value={selected} onChange={choose}>
        <option value="">Chọn sinh viên</option>
        {selectedMissing && <option value={selected}>{selected}</option>}
        {items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.student_code} – {item.full_name}
          </option>
        ))}
      </select>
      {resource.status === 'error' && (
        <p role="alert" className="status-error student-picker__error">
          Không tải được danh sách sinh viên.
        </p>
      )}
    </div>
  );
}
