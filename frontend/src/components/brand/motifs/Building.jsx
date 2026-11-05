import MotifFrame, { tokenColor } from './MotifFrame';

const WINDOW_COLUMNS = [28, 44, 60];
const WINDOW_ROWS = [32, 48, 64, 80];

export default function Building({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <polygon points="14,24 86,10 86,16 14,30" fill={tokenColor(fg)} />
      <rect x="20" y="24" width="60" height="76" fill={tokenColor(fg)} />
      {WINDOW_ROWS.flatMap((top) =>
        WINDOW_COLUMNS.map((left) => (
          <rect
            key={`${left}-${top}`}
            x={left}
            y={top}
            width="11"
            height="10"
            fill={tokenColor(bg)}
          />
        )),
      )}
    </MotifFrame>
  );
}
