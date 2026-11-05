import MotifFrame, { tokenColor } from './MotifFrame';

export default function DotTriangle({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <polygon points="0,100 100,0 100,100" fill={tokenColor(fg)} />
      <circle cx="30" cy="30" r="17" fill={tokenColor(fg)} />
      <circle cx="70" cy="72" r="12" fill={tokenColor(bg)} />
    </MotifFrame>
  );
}
