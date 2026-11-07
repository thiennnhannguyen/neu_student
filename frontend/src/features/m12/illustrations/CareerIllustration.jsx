import { MOTIFS } from '../../../components/brand/motifs';
import {
  AiIcon,
  BackendIcon,
  BaIcon,
  DataIcon,
  DevopsIcon,
  FrontendIcon,
  FullstackIcon,
  MobileIcon,
  QaIcon,
  SecurityIcon,
} from './icons';

const WIDTH = 320;
const HEIGHT = 200;
const CELL = HEIGHT / 3;

/**
 * Mỗi nghề: sắc nền của nhóm nghề, 6 ô họa tiết (3 trái, 3 phải) và biểu tượng riêng.
 * Ô họa tiết ghi [tên, nền, nét], đều là token của bộ nhận diện.
 */
export const ILLUSTRATIONS = {
  frontend: {
    tone: 1,
    Icon: FrontendIcon,
    cells: [
      ['QuarterCircle', 'tint', 'primary'],
      ['Stripes', 'primary-dark', 'mid'],
      ['Petals', 'accent', 'white'],
      ['DiagonalSplit', 'mid', 'primary'],
      ['CircleDiamond', 'tint', 'primary-dark'],
      ['HalfCircle', 'primary-dark', 'accent'],
    ],
  },
  backend: {
    tone: 1,
    Icon: BackendIcon,
    cells: [
      ['RisingBars', 'primary-dark', 'tint'],
      ['Gear', 'tint', 'primary'],
      ['Zigzag', 'mid', 'primary-dark'],
      ['CircuitCircle', 'accent', 'white'],
      ['DiagonalN', 'primary-dark', 'mid'],
      ['Stripes', 'tint', 'accent'],
    ],
  },
  fullstack: {
    tone: 1,
    Icon: FullstackIcon,
    cells: [
      ['Arcs', 'tint', 'primary'],
      ['DotTriangle', 'accent', 'white'],
      ['HalfCircle', 'primary-dark', 'mid'],
      ['FourPointStar', 'mid', 'white'],
      ['QuarterCircle', 'primary-dark', 'tint'],
      ['Zigzag', 'tint', 'primary'],
    ],
  },
  mobile: {
    tone: 1,
    Icon: MobileIcon,
    cells: [
      ['CircleDiamond', 'mid', 'primary-dark'],
      ['Petals', 'tint', 'accent'],
      ['DiagonalN', 'accent', 'white'],
      ['Arcs', 'primary-dark', 'mid'],
      ['DiagonalSplit', 'tint', 'accent'],
      ['RisingBars', 'mid', 'white'],
    ],
  },
  ai: {
    tone: 2,
    Icon: AiIcon,
    cells: [
      ['CircuitCircle', 'tint', 'primary'],
      ['FourPointStar', 'primary', 'tint'],
      ['Globe', 'mid', 'primary-dark'],
      ['Petals', 'primary', 'mid'],
      ['Arcs', 'accent', 'white'],
      ['CircleDiamond', 'tint', 'primary'],
    ],
  },
  data: {
    tone: 2,
    Icon: DataIcon,
    cells: [
      ['RisingBars', 'tint', 'primary'],
      ['QuarterCircle', 'accent', 'white'],
      ['Stripes', 'primary', 'mid'],
      ['DotTriangle', 'mid', 'white'],
      ['RisingBars', 'primary', 'tint'],
      ['HalfCircle', 'tint', 'accent'],
    ],
  },
  ba: {
    tone: 3,
    Icon: BaIcon,
    cells: [
      ['TwoPeople', 'tint', 'primary'],
      ['DiagonalSplit', 'primary-dark', 'accent'],
      ['Books', 'mid', 'primary-dark'],
      ['Zigzag', 'primary-dark', 'tint'],
      ['TwoPeople', 'accent', 'white'],
      ['Arcs', 'tint', 'primary'],
    ],
  },
  devops: {
    tone: 4,
    Icon: DevopsIcon,
    cells: [
      ['Gear', 'primary-dark', 'tint'],
      ['Arcs', 'tint', 'primary'],
      ['CircuitCircle', 'mid', 'primary-dark'],
      ['Globe', 'tint', 'accent'],
      ['Gear', 'primary', 'mid'],
      ['Stripes', 'primary-dark', 'tint'],
    ],
  },
  cybersecurity: {
    tone: 5,
    Icon: SecurityIcon,
    cells: [
      ['DiagonalN', 'primary', 'tint'],
      ['CircleDiamond', 'accent', 'white'],
      ['Zigzag', 'primary-dark', 'mid'],
      ['FourPointStar', 'primary', 'tint'],
      ['Stripes', 'mid', 'primary-dark'],
      ['CircuitCircle', 'primary-dark', 'accent'],
    ],
  },
  qa: {
    tone: 6,
    Icon: QaIcon,
    cells: [
      ['DotTriangle', 'tint', 'primary'],
      ['QuarterCircle', 'primary-dark', 'mid'],
      ['Petals', 'tint', 'primary'],
      ['HalfCircle', 'primary-dark', 'tint'],
      ['DiagonalSplit', 'tint', 'primary'],
      ['Zigzag', 'primary', 'white'],
    ],
  },
};

/** Nghề chưa có hình riêng: chỉ có nền họa tiết. */
const FALLBACK = {
  tone: 1,
  Icon: null,
  cells: [
    ['Arcs', 'tint', 'primary'],
    ['Stripes', 'primary-dark', 'mid'],
    ['QuarterCircle', 'accent', 'white'],
    ['HalfCircle', 'mid', 'primary-dark'],
    ['DiagonalSplit', 'tint', 'primary'],
    ['Zigzag', 'primary-dark', 'tint'],
  ],
};

function cellPosition(index) {
  const column = index < 3 ? 0 : WIDTH - CELL;
  return { x: column, y: (index % 3) * CELL };
}

/** Chỉ để trang trí nên ẩn khỏi trợ năng; tên nghề luôn là chữ thật ở ngoài hình. */
export default function CareerIllustration({ illustrationKey, className = '' }) {
  const { tone, Icon, cells } = ILLUSTRATIONS[illustrationKey] ?? FALLBACK;
  return (
    <svg
      className={`career-illustration ${className}`.trim()}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      aria-hidden="true"
      focusable="false"
      data-illustration={illustrationKey ?? 'fallback'}
    >
      <rect width={WIDTH} height={HEIGHT} fill={`var(--career-tone-${tone})`} />
      {cells.map(([name, bg, fg], index) => {
        const Motif = MOTIFS[name];
        return (
          <svg
            key={index}
            {...cellPosition(index)}
            width={CELL}
            height={CELL}
            viewBox="0 0 100 100"
          >
            <Motif bg={bg} fg={fg} />
          </svg>
        );
      })}
      {Icon && <Icon />}
    </svg>
  );
}
