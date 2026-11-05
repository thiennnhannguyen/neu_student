import { Navigate, useLocation } from 'react-router';
import BrandLogo from '../../components/BrandLogo';
import MotifMosaic from '../../components/brand/MotifMosaic';
import {
  LEFT_STRIP,
  MOBILE_BAND,
  RIGHT_STRIP,
  TABLET_BAND,
} from '../../components/brand/mosaicLayouts';
import { useAuth } from './AuthContext';
import LoginForm from './LoginForm';
import { safeRedirectPath } from './redirect';

export default function LoginPage() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === 'authenticated') {
    return <Navigate to={safeRedirectPath(location.state?.from)} replace />;
  }

  return (
    <main id="main" className="login-page">
      <div className="login-brand">
        <MotifMosaic {...TABLET_BAND} className="login-brand__band login-brand__band--tablet" />
        <MotifMosaic {...MOBILE_BAND} className="login-brand__band login-brand__band--mobile" />
        <MotifMosaic {...LEFT_STRIP} className="login-brand__strip" />
        <div className="login-brand__center">
          <span className="login-brand__word" aria-hidden="true">
            NEU
          </span>
          <div className="login-brand__copy">
            <BrandLogo decorative className="login-brand__logo" />
            <p className="login-brand__title">Nền tảng học tập sinh viên NEU</p>
            <p className="login-brand__subtitle">Phân tích học tập&nbsp;· Hỗ trợ người học</p>
          </div>
        </div>
        <MotifMosaic {...RIGHT_STRIP} className="login-brand__strip" />
      </div>
      <div className="login-panel">
        <LoginForm />
      </div>
    </main>
  );
}
