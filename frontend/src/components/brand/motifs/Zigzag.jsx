import MotifFrame, { tokenColor } from './MotifFrame';

const ROW_TOPS = [14, 42, 70];

function zigzagPoints(top) {
  const points = [];
  for (let step = 0; step <= 8; step += 1) {
    points.push(`${step * 12.5},${top + (step % 2 === 0 ? 14 : 0)}`);
  }
  return points.join(' ');
}

export default function Zigzag({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      {ROW_TOPS.map((top) => (
        <polyline
          key={top}
          points={zigzagPoints(top)}
          fill="none"
          stroke={tokenColor(fg)}
          strokeWidth="5"
          strokeLinejoin="miter"
        />
      ))}
    </MotifFrame>
  );
}
