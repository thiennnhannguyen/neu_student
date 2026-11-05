import { useState } from 'react';

export default function BrandLogo() {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return <span className="brand-fallback">NEU</span>;
  }
  return (
    <img
      className="app-header__logo"
      src="/brand/logo.svg"
      alt="Logo Đại học Kinh tế Quốc dân"
      onError={() => setFailed(true)}
    />
  );
}
