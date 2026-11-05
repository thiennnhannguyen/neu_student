import { useState } from 'react';
import { Navigate, useLocation } from 'react-router';
import BrandLogo from '../../components/BrandLogo';
import { useAuth } from './AuthContext';
import { safeRedirectPath } from './redirect';

export default function LoginPage() {
  const { status, login } = useAuth();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (status === 'authenticated') {
    return <Navigate to={safeRedirectPath(location.state?.from)} replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!username.trim() || !password) {
      setError('Vui lòng nhập tên đăng nhập và mật khẩu.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      await login(username.trim(), password);
    } catch (caught) {
      setError(caught.message);
      setPassword('');
      setSubmitting(false);
    }
  }

  return (
    <main id="main" className="login-page">
      <section className="card login-card">
        <div className="login-card__brand">
          <BrandLogo />
          <span className="mock-badge">Dữ liệu mẫu</span>
        </div>
        <h1>Đăng nhập</h1>
        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="login-username">Tên đăng nhập</label>
            <input
              id="login-username"
              name="username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              aria-describedby="login-error"
            />
          </div>
          <div className="field">
            <label htmlFor="login-password">Mật khẩu</label>
            <input
              id="login-password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              aria-describedby="login-error"
            />
          </div>
          <p id="login-error" className="status-error" aria-live="assertive" role="alert">
            {error}
          </p>
          <button type="submit" className="button button--full" disabled={submitting}>
            {submitting ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>
        </form>
      </section>
    </main>
  );
}
