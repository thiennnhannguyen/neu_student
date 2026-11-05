import { useState } from 'react';
import { withQuery } from './format';
import useApiResource from './useApiResource';
import { ResourceView, SidePanel } from './ui';

function GlossaryContent({ studentId, metricKey }) {
  const resource = useApiResource(
    withQuery('/api/m11/metrics-glossary', { student_id: studentId }),
  );
  return (
    <ResourceView
      resource={resource}
      loadingText="Đang tải giải thích..."
      errorText="Không tải được giải thích"
    >
      {(data) => {
        const item = data.items.find((entry) => entry.key === metricKey);
        if (!item) {
          return <p className="empty-state">Chưa có giải thích cho chỉ số này.</p>;
        }
        return (
          <dl className="glossary">
            <dt>Công thức</dt>
            <dd>{item.formula}</dd>
            <dt>Nguồn dữ liệu</dt>
            <dd>{item.source}</dd>
            <dt>Phiên bản quy chế</dt>
            <dd>{item.rule_version ?? 'Không xác định'}</dd>
            <dt>Ghi chú</dt>
            <dd>{item.note}</dd>
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
        className="metric-info"
        aria-label={`Giải thích: ${label}`}
        onClick={() => setOpen(true)}
      >
        i
      </button>
      {open && (
        <SidePanel title={label} onClose={() => setOpen(false)}>
          <GlossaryContent studentId={studentId} metricKey={metricKey} />
        </SidePanel>
      )}
    </>
  );
}
