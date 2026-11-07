/**
 * Thanh 3 đoạn. Cả thanh là toàn bộ môn của nghề (y của độ phủ): đoạn đậm đã đạt, đoạn nhạt còn
 * lại trong CTĐT, đoạn sọc ngoài CTĐT ngành bạn. Số % lớn vẫn theo Q92, không suy từ thanh này.
 */
const SEGMENTS = [
  { key: 'done', label: 'Đã đạt' },
  { key: 'remaining', label: 'Còn lại trong CTĐT' },
  { key: 'outside', label: 'Ngoài CTĐT ngành bạn' },
];

export function meterParts(done, coverage) {
  return {
    done,
    remaining: Math.max(coverage.numerator - done, 0),
    outside: coverage.denominator - coverage.numerator,
  };
}

export function meterText(parts) {
  return `${parts.done} môn đã đạt, ${parts.remaining} môn còn lại trong CTĐT, ${parts.outside} môn ngoài CTĐT ngành bạn`;
}

export function MeterLegend() {
  return (
    <ul className="career-meter-legend">
      {SEGMENTS.map((segment) => (
        <li key={segment.key}>
          <span className={`career-meter__segment career-meter__segment--${segment.key}`} />
          {segment.label}
        </li>
      ))}
    </ul>
  );
}

export default function CareerMeter({ done, coverage, label }) {
  const parts = meterParts(done, coverage);
  const total = coverage.denominator;
  return (
    <span
      className="career-meter"
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={Math.max(total, 1)}
      aria-valuenow={parts.done}
      aria-valuetext={total === 0 ? '—' : meterText(parts)}
    >
      {SEGMENTS.filter((segment) => parts[segment.key] > 0).map((segment) => (
        <span
          key={segment.key}
          className={`career-meter__segment career-meter__segment--${segment.key}`}
          style={{ flexGrow: parts[segment.key] }}
        />
      ))}
    </span>
  );
}
