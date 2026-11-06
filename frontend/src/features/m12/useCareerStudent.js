import { useCallback } from 'react';
import { useSearchParams } from 'react-router';
import { useAuth } from '../auth/AuthContext';
import { withQuery } from '../m11/format';

/** Sinh viên đang xem: của chính mình, hoặc do cố vấn, quản trị chọn trên thanh trên cùng. */
export default function useCareerStudent() {
  const { role } = useAuth();
  const [params] = useSearchParams();
  const isStudent = role === 'student';
  const studentId = isStudent ? null : params.get('student');
  const link = useCallback((path) => withQuery(path, { student: studentId }), [studentId]);
  return {
    isStudent,
    studentId,
    needsStudent: !isStudent && !studentId,
    query: { student_id: studentId },
    link,
  };
}
