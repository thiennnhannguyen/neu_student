import MotifFrame, { tokenColor } from './MotifFrame';

export default function DiagonalN({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <rect x="8" y="0" width="14" height="100" fill={tokenColor(fg)} />
      <rect x="78" y="0" width="14" height="100" fill={tokenColor(fg)} />
      <polygon points="22,0 40,0 78,70 78,100 72,100 22,16" fill={tokenColor(fg)} />
      <polygon points="50,0 62,0 78,30 78,52" fill={tokenColor(fg)} />
      <polygon points="22,48 58,100 40,100 22,74" fill={tokenColor(fg)} />
    </MotifFrame>
  );
}
