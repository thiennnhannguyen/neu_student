import MotifFrame, { tokenColor } from './MotifFrame';

const STRIPE_TOPS = [8, 28, 48, 68, 88];

export default function Stripes({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      {STRIPE_TOPS.map((top) => (
        <rect key={top} y={top} width="100" height="8" fill={tokenColor(fg)} />
      ))}
    </MotifFrame>
  );
}
