import MotifFrame, { tokenColor } from './MotifFrame';

export default function HalfCircle({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <path d="M50 4A46 46 0 0 1 50 96Z" fill={tokenColor(fg)} />
    </MotifFrame>
  );
}
