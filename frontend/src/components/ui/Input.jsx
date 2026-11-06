import { forwardRef } from 'react';

const Input = forwardRef(function Input({ className = '', ...rest }, ref) {
  return <input ref={ref} className={`ui-input ${className}`.trim()} {...rest} />;
});

export default Input;
