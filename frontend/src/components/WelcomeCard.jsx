import { WELCOME_MOSAIC } from './brand/mosaicLayouts';
import MotifMosaic from './brand/MotifMosaic';

export default function WelcomeCard({ name, line, action }) {
  return (
    <section className="welcome-card" aria-label="Lời chào">
      <div className="welcome-card__text">
        <p className="welcome-card__greeting">Chào {name}</p>
        {line && <p className="welcome-card__line">{line}</p>}
      </div>
      {action && <div className="welcome-card__action">{action}</div>}
      <MotifMosaic {...WELCOME_MOSAIC} className="welcome-card__mosaic" />
    </section>
  );
}
