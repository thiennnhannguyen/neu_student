import MotifFrame, { tokenColor } from './MotifFrame';

export default function Petals({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <path d="M47 92C14 88 4 50 6 10C34 16 50 48 47 92Z" fill={tokenColor(fg)} />
      <path d="M53 92C86 88 96 50 94 10C66 16 50 48 53 92Z" fill={tokenColor(fg)} />
    </MotifFrame>
  );
}
