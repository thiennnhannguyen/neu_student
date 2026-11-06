import { formatDateTime } from './format';

export function LevelBadge({ level, levels }) {
  const info = levels[level] ?? { label: level, icon: '?', tone: 'muted' };
  return (
    <span className={`level-badge level-badge--${info.tone}`}>
      <span aria-hidden="true">{info.icon}</span> {info.label}
    </span>
  );
}

export function ResourceView({ resource, loadingText, errorText, isEmpty, emptyText, children }) {
  if (resource.status === 'error') {
    return (
      <div role="alert">
        <p className="status-error">
          {errorText}: {resource.error.message}
        </p>
        <button type="button" className="button" onClick={resource.retry}>
          Thử lại
        </button>
      </div>
    );
  }
  if (resource.status !== 'ok') {
    return <p role="status">{loadingText}</p>;
  }
  if (isEmpty?.(resource.data)) {
    return <p className="empty-state">{emptyText}</p>;
  }
  return children(resource.data);
}

export function ReferenceLine({ semesterName, computedAt, ruleVersion }) {
  return (
    <p className="reference-line">
      Kỳ tham chiếu {semesterName ?? '—'} · Cập nhật {formatDateTime(computedAt)}
      {ruleVersion ? ` · Quy chế ${ruleVersion}` : ''}
    </p>
  );
}

export function DataWarnings({ warnings }) {
  if (!warnings?.length) {
    return null;
  }
  return (
    <details className="data-warnings">
      <summary>Cảnh báo dữ liệu ({warnings.length})</summary>
      <ul>
        {warnings.map((warning) => (
          <li key={`${warning.code}-${warning.course_id ?? ''}-${warning.semester_id ?? ''}`}>
            {warning.message}
          </li>
        ))}
      </ul>
    </details>
  );
}

export { default as SidePanel } from '../../components/ui/SidePanel';
