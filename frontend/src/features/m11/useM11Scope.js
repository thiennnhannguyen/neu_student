import { useCallback, useEffect } from 'react';
import { useSearchParams } from 'react-router';
import { useAuth } from '../auth/AuthContext';
import { withQuery } from './format';
import useApiResource from './useApiResource';

export const ALL_SEMESTERS = 'all';

/**
 * Sinh viên và kỳ đang xem, đọc từ URL. allowAll chỉ bật ở trang Kết quả (Q74).
 * enabled là false ở trang không thuộc M11: không gọi API, không đụng tới URL.
 */
export default function useM11Scope({ enabled = true, allowAll = false } = {}) {
  const { role } = useAuth();
  const [params, setParams] = useSearchParams();
  const picksStudent = role !== 'student';
  const studentId = picksStudent ? params.get('student') : null;
  const needsStudent = picksStudent && !studentId;
  const semesters = useApiResource(
    !enabled || needsStudent ? null : withQuery('/api/m11/semesters', { student_id: studentId }),
  );

  const raw = params.get('semester');
  const known = semesters.status === 'ok' && semesters.data.items.some((item) => item.id === raw);
  const isAll = allowAll && raw === ALL_SEMESTERS;
  const invalid =
    enabled &&
    raw !== null &&
    !isAll &&
    (raw === ALL_SEMESTERS || (semesters.status === 'ok' && !known));

  useEffect(() => {
    if (invalid) {
      setParams(
        (current) => {
          const next = new URLSearchParams(current);
          next.delete('semester');
          return next;
        },
        { replace: true },
      );
    }
  }, [invalid, setParams]);

  const setSemester = useCallback(
    (value) => {
      setParams((current) => {
        const next = new URLSearchParams(current);
        next.set('semester', value);
        next.delete('page');
        return next;
      });
    },
    [setParams],
  );

  const currentId = semesters.status === 'ok' ? semesters.data.current_id : null;
  let semesterId = currentId;
  if (isAll) {
    semesterId = ALL_SEMESTERS;
  } else if (known) {
    semesterId = raw;
  }

  return {
    allowAll,
    needsStudent,
    studentId,
    semesters,
    semesterId,
    setSemester,
    /** Tham số gửi lên API. Không có semester_id ở /grades nghĩa là tất cả các kỳ. */
    query: {
      student_id: studentId,
      semester_id: semesterId === ALL_SEMESTERS ? null : semesterId,
    },
  };
}
