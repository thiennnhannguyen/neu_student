import MotifFrame, { tokenColor } from './MotifFrame';

export default function QuarterCircle({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <path d="M0 0H100A100 100 0 0 1 0 100Z" fill={tokenColor(fg)} />
    </MotifFrame>
  );
}
