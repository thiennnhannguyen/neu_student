import { MOTIFS } from './motifs';

export const MOSAIC_FADE_MS = 240;
export const MOSAIC_MAX_DELAY_MS = 360;

function fadeDelay(index, total) {
  return total > 1 ? Math.round((index / (total - 1)) * MOSAIC_MAX_DELAY_MS) : 0;
}

/** Lưới họa tiết chỉ để trang trí. Hiện dần một lần khi tải trang, tổng thời gian không quá 600ms. */
export default function MotifMosaic({ rows, cols, layout, className = '' }) {
  if (layout.length !== rows * cols) {
    throw new Error(`Bố cục cần ${rows * cols} ô, nhận ${layout.length} ô.`);
  }
  return (
    <div
      className={`motif-mosaic ${className}`.trim()}
      aria-hidden="true"
      style={{ '--mosaic-cols': cols }}
    >
      {layout.map(([motif, bg, fg], index) => {
        const Motif = MOTIFS[motif];
        return (
          <div
            key={index}
            className="motif-mosaic__cell"
            style={{
              animationDuration: `${MOSAIC_FADE_MS}ms`,
              animationDelay: `${fadeDelay(index, layout.length)}ms`,
            }}
          >
            <Motif bg={bg} fg={fg} />
          </div>
        );
      })}
    </div>
  );
}
