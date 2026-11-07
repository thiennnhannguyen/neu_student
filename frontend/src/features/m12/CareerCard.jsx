import { Link } from 'react-router';
import CareerIllustration from './illustrations/CareerIllustration';
import CareerMeter from './CareerMeter';
import { lowCoverageText, percentText } from './labels';

/** Cả thẻ là một liên kết. Hai tỷ lệ tách riêng, không gộp (R8). */
export default function CareerCard({ item, link }) {
  const { career, course_progress: course, skill_progress: skill } = item;
  return (
    <Link
      to={link(`/m12/dinh-huong/nghe/${career.slug}`)}
      className={`career-card${item.is_primary ? ' career-card--primary' : ''}`}
    >
      <span className="career-card__media">
        <CareerIllustration illustrationKey={career.illustration_key} />
        {item.is_primary && <span className="career-card__goal">Mục tiêu của bạn</span>}
      </span>
      <span className="career-card__body">
        <strong className="career-card__name" title={career.display_name}>
          {career.display_name}
        </strong>
        <span className="career-card__en">
          {career.name_en ?? career.group}
          {career.is_mock && <span className="career-card__mock"> (mẫu)</span>}
        </span>
        {item.fits_major && (
          <span className="career-card__fit">Hợp ngành {item.fits_major.code}</span>
        )}
        <span className="career-card__meter">
          <span className="career-card__progress">
            <strong className="career-card__percent">{percentText(course.percent)}</strong>
            <span className="career-card__percent-label">học phần</span>
          </span>
          <CareerMeter
            done={course.numerator}
            coverage={item.coverage}
            label={`Học phần của ${career.display_name}`}
          />
          <span className="career-card__skill">
            Kỹ năng &amp; dự án {percentText(skill.percent)}
          </span>
          <span className="career-card__low">
            {item.low_coverage && lowCoverageText(item.coverage)}
          </span>
        </span>
      </span>
    </Link>
  );
}
