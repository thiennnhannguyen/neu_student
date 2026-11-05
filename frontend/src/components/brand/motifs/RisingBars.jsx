import MotifFrame, { tokenColor } from './MotifFrame';

export default function RisingBars({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <rect x="12" y="74" width="20" height="26" fill={tokenColor(fg)} />
      <rect x="40" y="58" width="20" height="42" fill={tokenColor(fg)} />
      <rect x="68" y="40" width="20" height="60" fill={tokenColor(fg)} />
      <polygon points="8,56 8,46 66,12 58,4 92,4 92,38 84,30 " fill={tokenColor(fg)} />
    </MotifFrame>
  );
}
