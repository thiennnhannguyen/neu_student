import MotifFrame, { tokenColor } from './MotifFrame';

export default function TwoPeople({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <circle cx="28" cy="26" r="16" fill={tokenColor(fg)} />
      <circle cx="72" cy="26" r="16" fill={tokenColor(fg)} />
      <path d="M6 94V70C6 56 16 46 28 46C40 46 47 56 47 70V94Z" fill={tokenColor(fg)} />
      <path d="M53 94V70C53 56 60 46 72 46C84 46 94 56 94 70V94Z" fill={tokenColor(fg)} />
    </MotifFrame>
  );
}
