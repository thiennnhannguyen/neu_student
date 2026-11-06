import MotifFrame, { tokenColor } from './MotifFrame';

const LATITUDES = ['M8 50H92', 'M16 30C34 38 66 38 84 30', 'M16 70C34 62 66 62 84 70'];

export default function Globe({ bg, fg }) {
  return (
    <MotifFrame bg={bg}>
      <circle cx="50" cy="50" r="44" fill={tokenColor(fg)} />
      {LATITUDES.map((line) => (
        <path key={line} d={line} fill="none" stroke={tokenColor(bg)} strokeWidth="6" />
      ))}
    </MotifFrame>
  );
}
