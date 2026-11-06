/** percent là số nguyên 0–100 do nơi gọi tính. valueText là chữ hiện bên phải nhãn. */
export default function ProgressBar({ label, percent, valueText }) {
  return (
    <div className="progress-bar">
      <p className="progress-bar__head">
        <span>{label}</span>
        <strong>{valueText}</strong>
      </p>
      <div
        className="progress-bar__track"
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
      >
        <div className="progress-bar__fill" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
