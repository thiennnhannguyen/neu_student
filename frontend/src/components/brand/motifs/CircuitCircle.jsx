import MotifFrame, { tokenColor } from './MotifFrame';

const TRACES = [
  'M50 14V86',
  'M50 32H70V24',
  'M50 50H78',
  'M50 68H68V78',
  'M50 40H30V30',
  'M50 62H26',
];
const NODES = [
  [70, 24],
  [78, 50],
  [68, 78],
  [30, 30],
  [26, 62],
];

export default function CircuitCircle({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <circle cx="50" cy="50" r="46" fill={tokenColor(fg)} />
      {TRACES.map((trace) => (
        <path key={trace} d={trace} fill="none" stroke={tokenColor(bg)} strokeWidth="4" />
      ))}
      {NODES.map(([x, y]) => (
        <circle key={`${x}-${y}`} cx={x} cy={y} r="5.5" fill={tokenColor(bg)} />
      ))}
    </MotifFrame>
  );
}
