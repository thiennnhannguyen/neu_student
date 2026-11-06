import { useRef } from 'react';
import Button from './Button';
import useFocusTrap from './useFocusTrap';

/** Hộp xác nhận: focus vào nút hủy, Tab không ra ngoài, Esc để hủy, đóng thì trả focus. */
export default function ConfirmDialog({
  title,
  confirmLabel,
  cancelLabel = 'Hủy',
  busy = false,
  error,
  onConfirm,
  onCancel,
  children,
}) {
  const dialogRef = useRef(null);
  const cancelRef = useRef(null);
  useFocusTrap(dialogRef, true, onCancel, cancelRef);

  return (
    // Nền chỉ bắt chuột để đóng; bàn phím đã có nút Hủy và phím Esc.
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div className="confirm-dialog__backdrop" onMouseDown={onCancel}>
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <div
        ref={dialogRef}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-body"
        className="confirm-dialog"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <h2 id="confirm-dialog-title" className="confirm-dialog__title">
          {title}
        </h2>
        <div id="confirm-dialog-body">{children}</div>
        {error && (
          <p role="alert" className="status-error">
            {error}
          </p>
        )}
        <div className="confirm-dialog__actions">
          <Button ref={cancelRef} variant="secondary" onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button loading={busy} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
