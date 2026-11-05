export const MOCK_NOTICE =
  'Sản phẩm bài tập lớn – không phải hệ thống chính thức của Đại học Kinh tế Quốc dân.';

export default function MockNotice({ className = '' }) {
  return <p className={`mock-notice ${className}`.trim()}>{MOCK_NOTICE}</p>;
}
