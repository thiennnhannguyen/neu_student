function Icon({ children }) {
  return (
    <svg
      className="login-icon"
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
      fill="currentColor"
    >
      {children}
    </svg>
  );
}

export function EyeIcon() {
  return (
    <Icon>
      <path d="M12 5C7 5 3 8.5 1 12c2 3.5 6 7 11 7s9-3.5 11-7c-2-3.5-6-7-11-7Zm0 12a5 5 0 1 1 0-10 5 5 0 0 1 0 10Zm0-2.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z" />
    </Icon>
  );
}

export function EyeOffIcon() {
  return (
    <Icon>
      <path d="M12 5C7 5 3 8.5 1 12c2 3.5 6 7 11 7s9-3.5 11-7c-2-3.5-6-7-11-7Zm0 12a5 5 0 1 1 0-10 5 5 0 0 1 0 10Z" />
      <polygon points="3.4,2 22,20.6 20.6,22 2,3.4" />
    </Icon>
  );
}

export function AlertIcon() {
  return (
    <Icon>
      <path d="M12 2 1 21h22L12 2Zm-1 7h2v6h-2V9Zm0 8h2v2h-2v-2Z" />
    </Icon>
  );
}
