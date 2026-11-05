import { useEffect, useRef } from 'react';
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

const FOCUSABLE = 'a[href], button:not([disabled]), input, select, summary, [tabindex="0"]';

/** Panel bên phải: focus vào nút đóng, Esc để đóng, Tab không ra ngoài, đóng thì trả focus. */
export function SidePanel({ title, onClose, children }) {
  const panelRef = useRef(null);
  const closeRef = useRef(null);

  useEffect(() => {
    const opener = document.activeElement;
    closeRef.current?.focus();
    return () => opener?.focus?.();
  }, []);

  function handleKeyDown(event) {
    if (event.key === 'Escape') {
      event.stopPropagation();
      onClose();
      return;
    }
    if (event.key !== 'Tab') {
      return;
    }
    const items = [...panelRef.current.querySelectorAll(FOCUSABLE)];
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return (
    // Nền và panel chỉ bắt chuột để đóng; bàn phím đã có nút Đóng và phím Esc.
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div className="side-panel__backdrop" onMouseDown={onClose}>
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="side-panel"
        onMouseDown={(event) => event.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        <div className="side-panel__header">
          <h2>{title}</h2>
          <button ref={closeRef} type="button" className="button button--ghost" onClick={onClose}>
            Đóng
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
