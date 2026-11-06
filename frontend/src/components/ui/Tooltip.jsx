import { useId } from 'react';

/**
 * Nút nhãn có chú thích gắn bằng aria-describedby. Chú thích hiện ngay dưới nút khi rê chuột
 * hoặc focus, không nổi lên trên, để không bị cắt trong vùng cuộn của bảng.
 */
export default function Tooltip({ label, icon: Icon, tone = 'warning', text }) {
  const id = useId();
  return (
    <span className="ui-tooltip">
      <button
        type="button"
        className={`badge badge--${tone} ui-tooltip__trigger`}
        aria-describedby={id}
      >
        {Icon && <Icon size={14} aria-hidden="true" />}
        {label}
      </button>
      <span role="tooltip" id={id} className="ui-tooltip__text">
        {text}
      </span>
    </span>
  );
}
