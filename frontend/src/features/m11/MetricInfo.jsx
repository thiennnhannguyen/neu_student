import { Info } from 'lucide-react';
import { useState } from 'react';
import { EmptyState, SidePanel } from '../../components/ui';
import { withQuery } from './format';
import useApiResource from './useApiResource';
import { ResourceView } from './ui';

function GlossaryContent({ studentId, metricKey }) {
  const resource = useApiResource(
    withQuery('/api/m11/metrics-glossary', { student_id: studentId }),
  );
  return (
    <ResourceView
      compact
      resource={resource}
      loadingText="Đang tải giải thích..."
      errorText="Không tải được giải thích"
    >
      {(data) => {
        const item = data.items.find((entry) => entry.key === metricKey);
        if (!item) {
          return <EmptyState compact heading="p" title="Chưa có giải thích cho chỉ số này." />;
        }
        return (
          <dl className="detail-list detail-list--stacked">
            <div>
              <dt>Công thức</dt>
              <dd>{item.formula}</dd>
            </div>
            <div>
              <dt>Nguồn dữ liệu</dt>
              <dd>{item.source}</dd>
            </div>
            <div>
              <dt>Phiên bản quy chế</dt>
              <dd>{item.rule_version ?? 'Không xác định'}</dd>
            </div>
            <div>
              <dt>Ghi chú</dt>
              <dd>{item.note}</dd>
            </div>
          </dl>
        );
      }}
    </ResourceView>
  );
}

export default function MetricInfo({ metricKey, label, studentId }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        className="icon-button icon-button--primary"
        aria-label={`Giải thích: ${label}`}
        onClick={() => setOpen(true)}
      >
        <Info size={18} aria-hidden="true" />
      </button>
      {open && (
        <SidePanel title={label} onClose={() => setOpen(false)}>
          <GlossaryContent studentId={studentId} metricKey={metricKey} />
        </SidePanel>
      )}
    </>
  );
}
