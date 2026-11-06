export default function Select({ className = '', children, ...rest }) {
  return (
    <select className={`ui-input ui-select ${className}`.trim()} {...rest}>
      {children}
    </select>
  );
}
