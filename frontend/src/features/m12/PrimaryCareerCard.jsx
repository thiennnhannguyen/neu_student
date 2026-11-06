import { Network } from 'lucide-react';
import { WELCOME_MOSAIC } from '../../components/brand/mosaicLayouts';
import MotifMosaic from '../../components/brand/MotifMosaic';
import { Badge, Button } from '../../components/ui';
import ProgressBars from './ProgressBars';

export default function PrimaryCareerCard({ primary, disclaimer, link }) {
  const { career } = primary;
  return (
    <section className="primary-career" aria-labelledby="primary-career-name">
      <div className="primary-career__body">
        <p className="primary-career__eyebrow">Nghề chính</p>
        <h2 id="primary-career-name" className="primary-career__name">
          {career.name}
        </h2>
        <p className="primary-career__field">{career.field}</p>
        <ProgressBars item={primary} disclaimer={disclaimer} withInfo />
        {primary.outside_curriculum_count > 0 && (
          <p className="primary-career__note">
            <Badge tone="outline">Ngoài CTĐT</Badge> {primary.outside_curriculum_count} học phần
            ngoài chương trình đào tạo của bạn, nên hỏi cố vấn.
          </p>
        )}
        <Button to={link(`/m12/dinh-huong/nghe/${career.id}`)} iconLeft={Network}>
          Xem cây nghề
        </Button>
      </div>
      <MotifMosaic {...WELCOME_MOSAIC} className="primary-career__mosaic" />
    </section>
  );
}
