/** Sidebar mang theo sinh viên và kỳ; "all" chỉ có ý nghĩa ở trang Kết quả nên không mang đi. */
export function carrySearch(search) {
  const current = new URLSearchParams(search);
  const next = new URLSearchParams();
  if (current.get('student')) {
    next.set('student', current.get('student'));
  }
  const semester = current.get('semester');
  if (semester && semester !== 'all') {
    next.set('semester', semester);
  }
  const text = next.toString();
  return text ? `?${text}` : '';
}
