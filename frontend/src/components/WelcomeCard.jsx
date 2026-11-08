import { WELCOME_MOSAIC } from './brand/mosaicLayouts';
import MotifMosaic from './brand/MotifMosaic';

/** `title` thay câu chào: Tổng quan ghi "Mã SV - Họ tên" (D-306); trang chung vẫn "Chào …". */
export default function WelcomeCard({ name, title, line, action }) {
  return (
    <section className="welcome-card" aria-label="Lời chào">
      <div className="welcome-card__text">
        <p className="welcome-card__greeting">{title ?? `Chào ${name}`}</p>
        {line && <p className="welcome-card__line">{line}</p>}
      </div>
      {action && <div className="welcome-card__action">{action}</div>}
      <MotifMosaic {...WELCOME_MOSAIC} className="welcome-card__mosaic" />
    </section>
  );
}
