/**
 * D-326: dấu tick dùng chung cho mọi trạng thái "đạt / xong": hình tròn xanh lá đặc, dấu tick trắng
 * (theo mẫu quản lý dự án gửi). Nhận props giống icon lucide (size, aria-hidden, role, aria-label).
 */
export default function CheckBadge({ size = 16, className = '', ...rest }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      focusable="false"
      className={`check-badge ${className}`.trim()}
      {...rest}
    >
      <circle cx="12" cy="12" r="12" fill="var(--check-badge-bg)" />
      <path
        d="M6.5 12.5l3.6 3.6 7.4-8"
        fill="none"
        stroke="var(--neu-white)"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
