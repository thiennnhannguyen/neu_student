const TOKENS = new Set(['primary', 'primary-dark', 'tint', 'mid', 'accent', 'white']);

/** Đổi tên token thành giá trị CSS. Mọi mã màu nằm trong tokens.css. */
export function tokenColor(name) {
  if (!TOKENS.has(name)) {
    throw new Error(`Token màu không hợp lệ: ${name}`);
  }
  return `var(--neu-${name})`;
}

/** Khung chung: ô vuông 100 x 100, chỉ để trang trí nên không vào cây trợ năng và không nhận focus. */
export default function MotifFrame({ bg, children }) {
  return (
    <svg
      className="motif"
      viewBox="0 0 100 100"
      aria-hidden="true"
      focusable="false"
      preserveAspectRatio="xMidYMid slice"
    >
      <rect width="100" height="100" fill={tokenColor(bg)} />
      {children}
    </svg>
  );
}
