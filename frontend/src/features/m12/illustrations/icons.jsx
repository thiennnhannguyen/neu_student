/* Biểu tượng trung tâm của từng nghề, vẽ bằng hình khối, tâm hình ở khoảng (160, 100). */
const W = 'var(--neu-white)';
const T = 'var(--neu-tint)';
const M = 'var(--neu-mid)';
const A = 'var(--neu-accent)';
const P = 'var(--neu-primary)';
const D = 'var(--neu-primary-dark)';

export function FrontendIcon() {
  return (
    <g>
      <rect x="84" y="42" width="152" height="116" rx="8" fill={W} />
      <path d="M84 50a8 8 0 0 1 8-8h136a8 8 0 0 1 8 8v12H84z" fill={T} />
      <circle cx="97" cy="52" r="4" fill={A} />
      <circle cx="110" cy="52" r="4" fill={M} />
      <circle cx="123" cy="52" r="4" fill={P} />
      <rect x="96" y="74" width="128" height="14" rx="3" fill={P} />
      <rect x="96" y="96" width="60" height="50" rx="4" fill={T} />
      <rect x="164" y="96" width="60" height="22" rx="4" fill={A} />
      <rect x="164" y="124" width="60" height="22" rx="4" fill={M} />
    </g>
  );
}

function ServerUnit({ y }) {
  return (
    <g>
      <rect x="82" y={y} width="104" height="32" rx="6" fill={W} />
      <circle cx="98" cy={y + 16} r="5" fill={A} />
      <circle cx="114" cy={y + 16} r="5" fill={M} />
      <rect x="130" y={y + 12} width="44" height="8" rx="4" fill={T} />
    </g>
  );
}

export function BackendIcon() {
  return (
    <g>
      <ServerUnit y={44} />
      <ServerUnit y={84} />
      <ServerUnit y={124} />
      <g fill="none" stroke={W} strokeWidth="7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M212 62c-10 0-10 6-10 14v12c0 7-5 12-12 12 7 0 12 5 12 12v12c0 8 0 14 10 14" />
        <path d="M222 62c10 0 10 6 10 14v12c0 7 5 12 12 12-7 0-12 5-12 12v12c0 8 0 14-10 14" />
      </g>
    </g>
  );
}

function Layer({ y, fill, children }) {
  return (
    <g>
      <polygon points={`160,${y} 236,${y + 30} 160,${y + 60} 84,${y + 30}`} fill={fill} />
      {children}
    </g>
  );
}

export function FullstackIcon() {
  return (
    <g>
      <Layer y={96} fill={M} />
      <Layer y={68} fill={A} />
      <Layer y={38} fill={W}>
        <polygon points="160,50 206,68 160,86 114,68" fill={T} />
        <polygon points="140,62 170,50 186,56 156,68" fill={P} />
      </Layer>
      <g fill={W}>
        <circle cx="120" cy="108" r="3.5" />
        <circle cx="132" cy="113" r="3.5" />
        <circle cx="120" cy="136" r="3.5" />
        <circle cx="132" cy="141" r="3.5" />
      </g>
    </g>
  );
}

export function MobileIcon() {
  return (
    <g>
      <rect x="118" y="26" width="84" height="148" rx="14" fill={W} />
      <rect x="126" y="40" width="68" height="118" rx="4" fill={T} />
      <rect x="148" y="31" width="24" height="4" rx="2" fill={M} />
      <circle cx="160" cy="165" r="4" fill={M} />
      <rect x="132" y="47" width="56" height="32" rx="5" fill={P} />
      <circle cx="146" cy="63" r="8" fill={W} />
      <rect x="160" y="57" width="22" height="5" rx="2.5" fill={T} />
      <rect x="160" y="66" width="16" height="5" rx="2.5" fill={M} />
      <rect x="132" y="85" width="26" height="26" rx="5" fill={A} />
      <rect x="162" y="85" width="26" height="26" rx="5" fill={M} />
      <rect x="132" y="117" width="56" height="10" rx="5" fill={W} />
      <rect x="132" y="133" width="56" height="18" rx="5" fill={A} />
    </g>
  );
}

const LEFT = [58, 100, 142];
const MIDDLE = [40, 80, 120, 160];
const RIGHT = [72, 128];

export function AiIcon() {
  const links = [
    ...LEFT.flatMap((a) => MIDDLE.map((b) => [100, a, 160, b])),
    ...MIDDLE.flatMap((a) => RIGHT.map((b) => [160, a, 220, b])),
  ];
  return (
    <g>
      <g stroke={M} strokeWidth="2">
        {links.map(([x1, y1, x2, y2]) => (
          <line key={`${x1}-${y1}-${y2}`} x1={x1} y1={y1} x2={x2} y2={y2} />
        ))}
      </g>
      {LEFT.map((y) => (
        <circle key={y} cx="100" cy={y} r="12" fill={T} />
      ))}
      {MIDDLE.map((y) => (
        <circle key={y} cx="160" cy={y} r="12" fill={A} stroke={W} strokeWidth="3" />
      ))}
      {RIGHT.map((y) => (
        <circle key={y} cx="220" cy={y} r="15" fill={W} />
      ))}
      <circle cx="220" cy="72" r="6" fill={A} />
      <circle cx="220" cy="128" r="6" fill={A} />
    </g>
  );
}

export function DataIcon() {
  return (
    <g>
      <rect x="92" y="108" width="24" height="46" rx="3" fill={M} />
      <rect x="124" y="88" width="24" height="66" rx="3" fill={T} />
      <rect x="156" y="98" width="24" height="56" rx="3" fill={M} />
      <rect x="188" y="62" width="24" height="92" rx="3" fill={W} />
      <rect x="82" y="154" width="156" height="5" rx="2.5" fill={W} />
      <polyline
        points="104,88 136,62 168,72 200,38 232,28"
        fill="none"
        stroke={A}
        strokeWidth="6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <g fill={W} stroke={A} strokeWidth="3">
        <circle cx="104" cy="88" r="5.5" />
        <circle cx="136" cy="62" r="5.5" />
        <circle cx="168" cy="72" r="5.5" />
        <circle cx="200" cy="38" r="5.5" />
      </g>
    </g>
  );
}

export function BaIcon() {
  return (
    <g>
      <rect x="78" y="36" width="58" height="28" rx="6" fill={W} />
      <polygon points="107,82 133,102 107,122 81,102" fill={A} stroke={W} strokeWidth="3" />
      <rect x="78" y="138" width="58" height="26" rx="13" fill={T} />
      <g fill="none" stroke={W} strokeWidth="4" strokeLinecap="round">
        <path d="M107 64v14" />
        <path d="M107 122v12" />
        <path d="M133 102h20" />
      </g>
      <polygon points="150,95 162,102 150,109" fill={W} />
      <rect x="168" y="42" width="72" height="118" rx="6" fill={W} />
      <rect x="168" y="42" width="72" height="20" rx="6" fill={P} />
      <g fill={T}>
        <rect x="176" y="72" width="16" height="10" rx="2" />
        <rect x="176" y="92" width="16" height="10" rx="2" />
        <rect x="176" y="112" width="16" height="10" rx="2" />
        <rect x="176" y="132" width="16" height="10" rx="2" />
      </g>
      <g fill={M}>
        <rect x="198" y="74" width="34" height="6" rx="3" />
        <rect x="198" y="94" width="26" height="6" rx="3" />
        <rect x="198" y="114" width="34" height="6" rx="3" />
        <rect x="198" y="134" width="22" height="6" rx="3" />
      </g>
    </g>
  );
}

const GEAR_TEETH = Array.from({ length: 8 }, (_, index) => index * 45);

export function DevopsIcon() {
  return (
    <g transform="translate(160 100) scale(0.86) translate(-160 -100)">
      <path
        d="M160 100c-18-30-34-40-52-40a40 40 0 0 0 0 80c18 0 34-10 52-40s34-40 52-40a40 40 0 0 1 0 80c-18 0-34-10-52-40z"
        fill="none"
        stroke={W}
        strokeWidth="13"
      />
      <polygon points="118,48 136,60 118,72" fill={T} />
      <polygon points="202,128 184,140 202,152" fill={T} />
      <g transform="translate(160 100)">
        {GEAR_TEETH.map((angle) => (
          <rect
            key={angle}
            x="-6"
            y="-34"
            width="12"
            height="14"
            rx="2"
            fill={A}
            transform={`rotate(${angle})`}
          />
        ))}
        <circle r="24" fill={A} stroke={W} strokeWidth="3" />
        <circle r="9" fill={W} />
      </g>
    </g>
  );
}

export function SecurityIcon() {
  return (
    <g>
      <path d="M160 24l64 22v50c0 40-26 66-64 80-38-14-64-40-64-80V46z" fill={W} />
      <path d="M160 38l50 17v42c0 31-20 52-50 64z" fill={T} />
      <path
        d="M140 92V78a20 20 0 0 1 40 0v14"
        fill="none"
        stroke={P}
        strokeWidth="9"
        strokeLinecap="round"
      />
      <rect x="128" y="90" width="64" height="48" rx="8" fill={P} />
      <circle cx="160" cy="108" r="7" fill={W} />
      <rect x="156.5" y="110" width="7" height="16" rx="3" fill={W} />
    </g>
  );
}

function TickRow({ y, done = true }) {
  return (
    <g>
      <rect x="92" y={y} width="20" height="20" rx="4" fill={done ? A : T} />
      {done && (
        <polyline
          points={`${96},${y + 10} ${101},${y + 15} ${108},${y + 5}`}
          fill="none"
          stroke={W}
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
      <rect x="120" y={y + 6} width="58" height="8" rx="4" fill={M} />
    </g>
  );
}

export function QaIcon() {
  return (
    <g>
      <rect x="80" y="32" width="112" height="136" rx="8" fill={W} />
      <rect x="112" y="24" width="48" height="16" rx="5" fill={T} />
      <TickRow y={52} />
      <TickRow y={80} />
      <TickRow y={108} />
      <TickRow y={136} done={false} />
      <circle cx="194" cy="112" r="30" fill={T} stroke={D} strokeWidth="8" />
      <circle cx="194" cy="112" r="16" fill={W} />
      <rect x="216" y="134" width="34" height="12" rx="6" fill={D} transform="rotate(45 220 138)" />
    </g>
  );
}
