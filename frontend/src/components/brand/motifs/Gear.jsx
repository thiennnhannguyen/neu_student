import MotifFrame, { tokenColor } from './MotifFrame';

const TEETH = 8;
const OUTER_RADIUS = 46;
const ROOT_RADIUS = 34;
const TOOTH_HALF_ANGLE = Math.PI / 14;
const ROOT_HALF_ANGLE = Math.PI / 9;

function polar(radius, angle) {
  const x = 50 + radius * Math.cos(angle);
  const y = 50 + radius * Math.sin(angle);
  return `${x.toFixed(2)},${y.toFixed(2)}`;
}

const GEAR_POINTS = Array.from({ length: TEETH }, (_, index) => {
  const center = (index * 2 * Math.PI) / TEETH;
  return [
    polar(ROOT_RADIUS, center - ROOT_HALF_ANGLE),
    polar(OUTER_RADIUS, center - TOOTH_HALF_ANGLE),
    polar(OUTER_RADIUS, center + TOOTH_HALF_ANGLE),
    polar(ROOT_RADIUS, center + ROOT_HALF_ANGLE),
  ].join(' ');
}).join(' ');

export default function Gear({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <polygon points={GEAR_POINTS} fill={tokenColor(fg)} />
      <circle cx="50" cy="50" r="15" fill={tokenColor(bg)} />
    </MotifFrame>
  );
}
