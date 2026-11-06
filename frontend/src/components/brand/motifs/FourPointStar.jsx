import MotifFrame, { tokenColor } from './MotifFrame';

export default function FourPointStar({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <path
        d="M50 4C54 34 66 46 96 50C66 54 54 66 50 96C46 66 34 54 4 50C34 46 46 34 50 4Z"
        fill={tokenColor(fg)}
      />
    </MotifFrame>
  );
}
