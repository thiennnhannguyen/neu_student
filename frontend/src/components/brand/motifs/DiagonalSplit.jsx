import MotifFrame, { tokenColor } from './MotifFrame';

export default function DiagonalSplit({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <polygon points="0,100 100,0 100,100" fill={tokenColor(fg)} />
    </MotifFrame>
  );
}
