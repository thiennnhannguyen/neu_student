import MotifFrame, { tokenColor } from './MotifFrame';

export default function CircleDiamond({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <circle cx="50" cy="50" r="46" fill={tokenColor(fg)} />
      <polygon points="50,20 80,50 50,80 20,50" fill={tokenColor(bg)} />
    </MotifFrame>
  );
}
