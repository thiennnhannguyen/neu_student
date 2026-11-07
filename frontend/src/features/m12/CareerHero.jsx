import { Badge, InfoPopover } from '../../components/ui';
import CareerIllustration from './illustrations/CareerIllustration';
import CareerMeter, { MeterLegend } from './CareerMeter';
import { groupLabel, METER_NOTE, NOT_RECRUITMENT, RATE_NOTE } from './labels';
import ProgressRing from './ProgressRing';

function Fractions({ course, skill, disclaimer }) {
  return (
    <InfoPopover label="Giải thích tỷ lệ">
      {course.formula}; {skill.formula}. {RATE_NOTE} {METER_NOTE} {disclaimer ?? NOT_RECRUITMENT}.
    </InfoPopover>
  );
}

/**
 * Phần giới thiệu nghề. Nội dung đều từ dữ liệu nghề để landing page sau này dùng lại:
 * phần theo sinh viên (progress, action) là tùy chọn.
 */
export default function CareerHero({ profile, progress, action, isPrimary, fit }) {
  return (
    <section className="career-hero" aria-labelledby="career-hero-title">
      <div className="career-hero__media">
        <CareerIllustration illustrationKey={profile.illustration_key} />
      </div>
      <div className="career-hero__body">
        <p className="career-hero__group">{groupLabel(profile.group)}</p>
        <h1 id="career-hero-title">{profile.display_name}</h1>
        <p className="career-hero__en">
          {profile.name_en}
          {profile.is_mock && <span className="career-card__mock"> (mẫu)</span>}
        </p>
        {profile.tagline && <p className="career-hero__tagline">{profile.tagline}</p>}
        {profile.objective && (
          <p className="career-hero__objective">
            <strong>Mục tiêu đầu ra: </strong>
            {profile.objective}
          </p>
        )}
        <p className="career-hero__chips">
          {isPrimary && <Badge tone="info">Mục tiêu của bạn</Badge>}
          {fit && <Badge tone="outline">Phù hợp với ngành của bạn: {fit.code}</Badge>}
        </p>
        {profile.major_fit?.note && <p className="career-hero__note">{profile.major_fit.note}</p>}
        {action}
      </div>
      {progress && (
        <div className="career-hero__progress">
          <div className="career-hero__rings">
            <ProgressRing percent={progress.course.percent} label="Học phần" />
            <ProgressRing percent={progress.skill.percent} label="Kỹ năng & dự án" />
            <Fractions {...progress} />
          </div>
          <div className="career-hero__meter">
            <CareerMeter
              done={progress.course.numerator}
              coverage={progress.coverage}
              label={`Học phần của ${profile.display_name}`}
            />
            <MeterLegend />
          </div>
          <p className="career-hero__coverage">
            Ngành của bạn có {progress.coverage.numerator}/{progress.coverage.denominator} môn của
            nghề
          </p>
        </div>
      )}
    </section>
  );
}
