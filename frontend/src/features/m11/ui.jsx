import { Disclosure, EmptyState, ErrorState, Skeleton } from '../../components/ui';
import { formatDateTime } from './format';

/** compact: nằm trong Card hoặc panel. Bản đầy đủ dùng cho khoảng trống của cả trang. */
export function ResourceView({
  resource,
  loadingText,
  errorText,
  isEmpty,
  emptyText,
  compact = false,
  children,
}) {
  if (resource.status === 'error') {
    return (
      <ErrorState
        compact={compact}
        heading={compact ? 'p' : undefined}
        title={errorText}
        description={resource.error.message}
        onRetry={resource.retry}
      />
    );
  }
  if (resource.status !== 'ok') {
    return (
      <div role="status" className="resource-loading">
        <span className="visually-hidden">{loadingText}</span>
        <Skeleton />
        <Skeleton width="70%" />
        <Skeleton width="40%" />
      </div>
    );
  }
  if (isEmpty?.(resource.data)) {
    return <EmptyState compact={compact} heading={compact ? 'p' : undefined} title={emptyText} />;
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
    <Disclosure summary={`Cảnh báo dữ liệu (${warnings.length})`}>
      <ul>
        {warnings.map((warning) => (
          <li key={`${warning.code}-${warning.course_id ?? ''}-${warning.semester_id ?? ''}`}>
            {warning.message}
          </li>
        ))}
      </ul>
    </Disclosure>
  );
}
