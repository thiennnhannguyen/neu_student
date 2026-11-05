import MotifFrame, { tokenColor } from './MotifFrame';

const RADII = [18, 38, 58, 78];

export default function Arcs({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      {RADII.map((radius) => (
        <path
          key={radius}
          d={`M${50 - radius} 100A${radius} ${radius} 0 0 1 ${50 + radius} 100`}
          fill="none"
          stroke={tokenColor(fg)}
          strokeWidth="9"
        />
      ))}
    </MotifFrame>
  );
}
