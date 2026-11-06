import MotifFrame, { tokenColor } from './MotifFrame';

/** Chữ K ghép từ khối hình, không phải ký tự chữ. */
export default function LetterK({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <rect x="10" y="6" width="26" height="88" fill={tokenColor(fg)} />
      <path
        d="M92 6C60 8 44 26 40 50C44 74 60 92 92 94V70C74 68 66 60 64 50C66 40 74 32 92 30Z"
        fill={tokenColor(fg)}
      />
    </MotifFrame>
  );
}
