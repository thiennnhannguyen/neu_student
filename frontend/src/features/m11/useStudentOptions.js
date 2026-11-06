import { useState } from 'react';
import { useSearchParams } from 'react-router';
import { useAuth } from '../auth/AuthContext';
import { withQuery } from './format';
import useApiResource from './useApiResource';

const SOURCES = { advisor: '/api/advisor/students', admin: '/api/admin/students' };

/** Danh sách sinh viên cho ô chọn trên máy tính và tấm chọn trên điện thoại. Sinh viên chọn lưu ở URL. */
export default function useStudentOptions() {
  const { role } = useAuth();
  const [params, setParams] = useSearchParams();
  const [keyword, setKeyword] = useState('');
  const source = SOURCES[role];
  const resource = useApiResource(
    source ? withQuery(source, { q: keyword.trim(), page_size: 100 }) : null,
  );

  const selected = params.get('student') ?? '';
  const items = resource.status === 'ok' ? resource.data.items : [];
  const selectedItem = items.find((item) => item.id === selected);

  function choose(value) {
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

  return {
    enabled: Boolean(source),
    canSearchInline: role === 'admin',
    keyword,
    setKeyword,
    items,
    selected,
    selectedMissing: Boolean(selected) && !selectedItem,
    selectedCode: selectedItem?.student_code ?? selected,
    failed: resource.status === 'error',
    choose,
  };
}
