import { InfoPopover, ProgressBar } from '../../components/ui';
import { percentOf } from './labels';

const NOTE =
  'Tử số là số học phần đã đạt, gồm cả đạt qua tương đương và miễn; môn đang học không được tính. Kỹ năng và dự án chỉ tính khi minh chứng đã được duyệt. Mẫu số là số yêu cầu riêng biệt của nghề, môn ở nhiều nhóm chỉ đếm một lần.';

function Bar({ label, progress }) {
  return (
    <ProgressBar
      label={label}
      percent={percentOf(progress)}
      valueText={progress.denominator ? progress.formula : 'Chưa có yêu cầu'}
    />
  );
}

/** Hai tỷ lệ luôn tách riêng (R8). */
export default function ProgressBars({ item, disclaimer, withInfo = false }) {
  return (
    <div className="career-progress">
      <Bar label="Học phần" progress={item.course_progress} />
      <Bar label="Kỹ năng & dự án" progress={item.skill_progress} />
      {withInfo && (
        <p className="career-progress__info">
          <span>Cách tính tỷ lệ</span>
          <InfoPopover label="Giải thích tỷ lệ">
            {NOTE} {disclaimer}.
          </InfoPopover>
        </p>
      )}
    </div>
  );
}
