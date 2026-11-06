import MotifFrame, { tokenColor } from './MotifFrame';

const PAGES = [
  'M50 34C38 22 22 18 8 20V34C22 32 38 36 50 48',
  'M50 34C62 22 78 18 92 20V34C78 32 62 36 50 48',
];

/** Ba quyển sách: hai trang mở phía trên, gáy sách phía dưới. */
export default function Books({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      {PAGES.map((page) => (
        <path key={page} d={page} fill={tokenColor(fg)} />
      ))}
      <path d="M8 44C24 42 40 46 50 58C60 46 76 42 92 44V90H8Z" fill={tokenColor(fg)} />
    </MotifFrame>
  );
}
