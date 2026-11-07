import { Link } from 'react-router';
import CareerIllustration from './illustrations/CareerIllustration';
import { LOW_COVERAGE, percentText } from './labels';

/** Cả thẻ là một liên kết. Hai tỷ lệ tách riêng, không gộp (R8). */
export default function CareerCard({ item, link }) {
  const { career, course_progress: course, skill_progress: skill } = item;
  const percent = course.percent;
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
        <strong className="career-card__name">{career.display_name}</strong>
        <span className="career-card__en">
          {career.name_en ?? career.group}
          {career.is_mock && <span className="career-card__mock"> (mẫu)</span>}
        </span>
        {item.fits_major && (
          <span className="career-card__fit">Hợp ngành {item.fits_major.code}</span>
        )}
        <span className="career-card__progress">
          <strong className="career-card__percent">{percentText(percent)}</strong>
          <span className="career-card__percent-label">học phần</span>
        </span>
        <span
          className="career-card__track"
          role="progressbar"
          aria-label={`Học phần của ${career.display_name}`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent ?? 0}
          aria-valuetext={percentText(percent)}
        >
          <span className="career-card__fill" style={{ width: `${percent ?? 0}%` }} />
        </span>
        <span className="career-card__skill">Kỹ năng &amp; dự án {percentText(skill.percent)}</span>
        {item.low_coverage && <span className="career-card__low">{LOW_COVERAGE}</span>}
      </span>
    </Link>
  );
}
