export function initialsOf(name) {
  const words = name
    .replace(/\(.*?\)/g, '')
    .trim()
    .split(/\s+/)
    .filter((word) => /^\p{L}/u.test(word));
  if (words.length === 0) {
    return '?';
  }
  const first = words[0][0];
  const last = words.length > 1 ? words[words.length - 1][0] : '';
  return `${first}${last}`.toUpperCase();
}

/** Chỉ trang trí: tên luôn hiện bên cạnh. size: sm, md, lg. */
export default function Avatar({ name, size = 'md' }) {
  return (
    <span className={`avatar avatar--${size}`} aria-hidden="true">
      {initialsOf(name)}
    </span>
  );
}
