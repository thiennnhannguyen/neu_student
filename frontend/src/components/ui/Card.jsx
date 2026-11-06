export default function Card({
  title,
  actions,
  footer,
  className = '',
  as: Tag = 'section',
  children,
  ...rest
}) {
  return (
    <Tag className={`ui-card ${className}`.trim()} {...rest}>
      {(title || actions) && (
        <div className="ui-card__header">
          {title && <h2 className="ui-card__title">{title}</h2>}
          {actions}
        </div>
      )}
      <div className="ui-card__body">{children}</div>
      {footer && <div className="ui-card__footer">{footer}</div>}
    </Tag>
  );
}
