import { Loader2 } from 'lucide-react';
import { forwardRef } from 'react';
import { Link } from 'react-router';

/** variant: primary, secondary, ghost, danger. size: sm, md, lg. Có `to` thì là liên kết. */
const Button = forwardRef(function Button(
  {
    variant = 'primary',
    size = 'md',
    loading = false,
    iconLeft: IconLeft,
    iconRight: IconRight,
    to,
    type = 'button',
    className = '',
    children,
    disabled,
    ...rest
  },
  ref,
) {
  const classes = `btn btn--${variant} btn--${size} ${className}`.trim();
  const content = (
    <>
      {loading ? (
        <Loader2 className="spinner" size={16} aria-hidden="true" />
      ) : (
        IconLeft && <IconLeft size={16} aria-hidden="true" />
      )}
      {children}
      {IconRight && <IconRight size={16} aria-hidden="true" />}
    </>
  );
  if (to) {
    return (
      <Link to={to} className={classes} {...rest}>
        {content}
      </Link>
    );
  }
  return (
    <button ref={ref} type={type} className={classes} disabled={disabled || loading} {...rest}>
      {content}
    </button>
  );
});

export default Button;
