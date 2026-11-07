import { useState } from 'react';
import BrandLogo from '../../components/BrandLogo';
import { useAuth } from './AuthContext';
import { AlertIcon, EyeIcon, EyeOffIcon } from './LoginIcons';

export default function LoginForm({ username, setUsername, passwordRef }) {
  const { login } = useAuth();
  const [password, setPassword] = useState('');
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [capsLockOn, setCapsLockOn] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

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

  function updateCapsLock(event) {
    setCapsLockOn(event.getModifierState('CapsLock'));
  }

  return (
    <section className="login-card">
      <div className="login-card__badge">
        <span className="mock-badge">Dữ liệu mẫu</span>
      </div>
      <div className="login-card__brand">
        <BrandLogo />
        <p className="login-card__school">
          <span>ĐẠI HỌC KINH TẾ QUỐC DÂN</span>
          <span>NATIONAL ECONOMICS UNIVERSITY</span>
        </p>
      </div>
      <h1>Đăng nhập</h1>
      <p className="login-card__intro">Dùng tài khoản được cấp cho bạn</p>
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
          <div className="password-input">
            <input
              ref={passwordRef}
              id="login-password"
              name="password"
              type={passwordVisible ? 'text' : 'password'}
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              onKeyDown={updateCapsLock}
              onKeyUp={updateCapsLock}
              onBlur={() => setCapsLockOn(false)}
              aria-describedby="login-error login-caps"
            />
            <button
              type="button"
              className="password-input__toggle"
              aria-label={passwordVisible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
              aria-pressed={passwordVisible}
              onClick={() => setPasswordVisible((value) => !value)}
            >
              {passwordVisible ? <EyeOffIcon /> : <EyeIcon />}
            </button>
          </div>
          <p id="login-caps" className="field__hint" aria-live="polite">
            {capsLockOn ? 'Caps Lock đang bật' : ''}
          </p>
        </div>
        <p
          id="login-error"
          className={`login-alert${error ? ' login-alert--visible' : ''}`}
          aria-live="assertive"
          role="alert"
        >
          {error && <AlertIcon />}
          {error}
        </p>
        <button type="submit" className="button button--full" disabled={submitting}>
          {submitting && <span className="spinner" aria-hidden="true" />}
          {submitting ? 'Đang đăng nhập…' : 'Đăng nhập'}
        </button>
      </form>
    </section>
  );
}
