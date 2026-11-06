import { Link } from 'react-router';
import { Card } from '../../components/ui';
import ProgressBars from './ProgressBars';

/** Nghề liên quan chỉ là gợi ý (R10). closeness null khi chưa có nghề chính. */
export default function RelatedCareerCard({ item, link, disclaimer }) {
  const { career, closeness } = item;
  return (
    <Card as="article" className="related-career">
      <h3 className="related-career__name">
        <Link to={link(`/m12/dinh-huong/nghe/${career.id}`)}>{career.name}</Link>
      </h3>
      <p className="related-career__field">{career.field}</p>
      {closeness && (
        <p className="related-career__closeness">
          {closeness.numerator}/{closeness.denominator} yêu cầu trùng với nghề chính
        </p>
      )}
      <ProgressBars item={item} disclaimer={disclaimer} />
    </Card>
  );
}
