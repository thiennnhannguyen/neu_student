import { Link } from 'react-router';
import { Badge, SidePanel, StatusChip } from '../../components/ui';
import useApiResource from '../m11/useApiResource';
import { ResourceView } from '../m11/ui';
import { chipStatus, kindLabel, NO_CODE } from './labels';

function viaText(child) {
  return child.via_course ? `Đạt qua tương đương: ${child.via_course.code ?? NO_CODE}` : null;
}

function Details({ child, detail, link }) {
  const isCourse = child.kind === 'course';
  return (
    <>
      <p className="requirement-panel__status">
        <StatusChip status={chipStatus(child.kind, child.status)} />
        {child.outside_curriculum && <Badge tone="outline">Ngoài CTĐT</Badge>}
      </p>
      {child.via_course && <p className="requirement-panel__via">{viaText(child)}</p>}
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
            <div>
              <dt>Tiên quyết</dt>
              <dd>
                {detail.prerequisites.length === 0
                  ? 'Không có'
                  : detail.prerequisites
                      .map((item) => `${item.code ?? NO_CODE} ${item.name}`)
                      .join(', ')}
              </dd>
            </div>
          </>
        )}
        {detail.short_desc && (
          <div>
            <dt>Mô tả</dt>
            <dd>{detail.short_desc}</dd>
          </div>
        )}
      </dl>
      <h3 className="requirement-panel__heading">Cũng có ở các nghề</h3>
      {detail.other_careers.length === 0 ? (
        <p>Chỉ có ở nghề này.</p>
      ) : (
        <ul className="requirement-panel__careers">
          {detail.other_careers.map((career) => (
            <li key={career.id}>
              <Link to={link(`/m12/dinh-huong/nghe/${career.id}`)}>{career.name}</Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

export default function RequirementPanel({ child, link, onClose }) {
  const resource = useApiResource(`/api/m12/requirements/${child.id}`);
  return (
    <SidePanel title={child.title} onClose={onClose}>
      <ResourceView
        compact
        resource={resource}
        loadingText="Đang tải chi tiết..."
        errorText="Không tải được chi tiết"
      >
        {(detail) => <Details child={child} detail={detail} link={link} />}
      </ResourceView>
    </SidePanel>
  );
}
