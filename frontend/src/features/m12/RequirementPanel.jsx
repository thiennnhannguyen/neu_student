import { Link } from 'react-router';
import { Badge, SidePanel, StatusChip } from '../../components/ui';
import useApiResource from '../m11/useApiResource';
import { ResourceView } from '../m11/ui';
import { chipStatus, kindLabel, NO_CODE, NOT_IN_PROGRAM, priorityLabel, typeLabel } from './labels';

function courseText(item) {
  return `${item.code ?? NO_CODE} ${item.name}`;
}

function PrerequisiteRows({ items }) {
  const official = items.filter((item) => item.kind !== 'recommended_order');
  const recommended = items.filter((item) => item.kind === 'recommended_order');
  return (
    <>
      <div>
        <dt>Tiên quyết</dt>
        <dd>{official.length === 0 ? 'Không có' : official.map(courseText).join(', ')}</dd>
      </div>
      {recommended.length > 0 && (
        <div>
          <dt>Thứ tự học khuyến nghị</dt>
          <dd>
            Nên học trước: {recommended.map(courseText).join(', ')}.
            <span className="requirement-panel__source"> {recommended[0].source}.</span>
          </dd>
        </div>
      )}
    </>
  );
}

function Details({ child, detail, link }) {
  const isCourse = child.kind === 'course';
  const type = typeLabel(child.requirement_type);
  return (
    <>
      <p className="requirement-panel__status">
        <StatusChip status={chipStatus(child.kind, child.status)} />
        {child.outside_curriculum && <Badge tone="outline">Ngoài CTĐT</Badge>}
      </p>
      {child.via_course && (
        <p className="requirement-panel__via">
          Đạt qua tương đương: {child.via_course.code ?? NO_CODE}
        </p>
      )}
      {child.purpose && (
        <p className="requirement-panel__purpose">
          <strong>Học để làm gì? </strong>
          {child.purpose}
        </p>
      )}
      {child.data_warning && <p className="requirement-panel__warning">{child.data_warning}</p>}
      <dl className="detail-list">
        <div>
          <dt>Loại</dt>
          <dd>{kindLabel(child.kind)}</dd>
        </div>
        {isCourse && (
          <>
            <div>
              <dt>Mã</dt>
              <dd>{detail.code ?? NO_CODE}</dd>
            </div>
            <div>
              <dt>Tín chỉ</dt>
              <dd>{detail.credits}</dd>
            </div>
            {type && (
              <div>
                <dt>BB/TC</dt>
                <dd>{type}</dd>
              </div>
            )}
            {child.requirement_type && (
              <div>
                <dt>Học kỳ chính thức theo CTĐT</dt>
                <dd>{child.planned_semester ? `HK ${child.planned_semester}` : 'Không ghi'}</dd>
              </div>
            )}
            <PrerequisiteRows items={detail.prerequisites} />
            {detail.equivalents.length > 0 && (
              <div>
                <dt>Tương đương</dt>
                <dd>{detail.equivalents.map(courseText).join(', ')}</dd>
              </div>
            )}
          </>
        )}
        {detail.short_desc && (
          <div>
            <dt>Mô tả</dt>
            <dd>{detail.short_desc}</dd>
          </div>
        )}
      </dl>
      <h3 className="requirement-panel__heading">Các nghề khác dùng môn này</h3>
      {detail.other_careers.length === 0 ? (
        <p>Chỉ có ở nghề này.</p>
      ) : (
        <ul className="requirement-panel__careers">
          {detail.other_careers.map((career) => (
            <li key={career.id}>
              <Link to={link(`/m12/dinh-huong/nghe/${career.slug}`)}>{career.name}</Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

function FetchedDetails({ child, link }) {
  const resource = useApiResource(`/api/m12/requirements/${child.id}`);
  return (
    <ResourceView
      compact
      resource={resource}
      loadingText="Đang tải chi tiết..."
      errorText="Không tải được chi tiết"
    >
      {(detail) => <Details child={child} detail={detail} link={link} />}
    </ResourceView>
  );
}

function AbsentDetails({ child }) {
  const priority = priorityLabel(child.priority);
  return (
    <>
      <p className="requirement-panel__status">
        <StatusChip status="not_in_program" />
      </p>
      {child.purpose && (
        <p className="requirement-panel__purpose">
          <strong>Học để làm gì? </strong>
          {child.purpose}
        </p>
      )}
      {priority && <p>Mức ưu tiên: {priority}.</p>}
      <p>
        {NOT_IN_PROGRAM}, nên không tính vào tỷ lệ học phần. Xem phần tự học tương đương ở tab Kỹ
        năng &amp; dự án.
      </p>
    </>
  );
}

export default function RequirementPanel({ child, link, onClose, inline = false }) {
  return (
    <SidePanel title={child.title} onClose={onClose} inline={inline}>
      {child.not_in_program ? (
        <AbsentDetails child={child} />
      ) : (
        <FetchedDetails child={child} link={link} />
      )}
    </SidePanel>
  );
}
