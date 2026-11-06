import { cloneElement } from 'react';

/** Gắn label, gợi ý, lỗi vào ô nhập. errors là danh sách thông báo từ API. */
export default function FormField({ id, label, hint, errors, className = '', children }) {
  const hintId = hint ? `${id}-hint` : null;
  const errorId = errors ? `${id}-error` : null;
  const describedBy = [errorId, hintId].filter(Boolean).join(' ') || undefined;
  return (
    <div className={`form-field ${className}`.trim()}>
      <label htmlFor={id}>{label}</label>
      {cloneElement(children, {
        id,
        'aria-invalid': errors ? 'true' : undefined,
        'aria-describedby': describedBy,
      })}
      {hint && (
        <p id={hintId} className="form-field__hint">
          {hint}
        </p>
      )}
      {errors && (
        <p id={errorId} className="form-field__error">
          {errors.join(' ')}
        </p>
      )}
    </div>
  );
}
