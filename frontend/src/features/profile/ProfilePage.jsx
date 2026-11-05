import { useCallback, useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';

const NO_VALUE = 'Chưa có';

function contactForm(profile) {
  return {
    contact_email: profile.contact_email ?? '',
    contact_phone: profile.contact_phone ?? '',
  };
}

function ContactField({ id, label, type, autoComplete, value, errors, onChange }) {
  const errorId = `${id}-error`;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type={type}
        autoComplete={autoComplete}
        value={value}
        onChange={onChange}
        aria-invalid={errors ? 'true' : undefined}
        aria-describedby={errors ? errorId : undefined}
      />
      {errors && (
        <p id={errorId} className="status-error field__error">
          {errors.join(' ')}
        </p>
      )}
    </div>
  );
}

export default function ProfilePage() {
  const [state, setState] = useState({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const [form, setForm] = useState({ contact_email: '', contact_phone: '' });
  const [saving, setSaving] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [formMessage, setFormMessage] = useState({ kind: null, text: '' });

  useEffect(() => {
    const controller = new AbortController();
    apiRequest('/api/students/me', { signal: controller.signal })
      .then((profile) => {
        setState({ status: 'ok', profile });
        setForm(contactForm(profile));
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setState({ status: 'error', message: error.message });
        }
      });
    return () => controller.abort();
  }, [attempt]);

  const retry = useCallback(() => {
    setState({ status: 'loading' });
    setAttempt((value) => value + 1);
  }, []);

  function updateField(name) {
    return (event) => setForm((current) => ({ ...current, [name]: event.target.value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setFieldErrors({});
    setFormMessage({ kind: null, text: '' });
    setSaving(true);
    try {
      const profile = await apiRequest('/api/students/me/contact', {
        method: 'PATCH',
        body: {
          contact_email: form.contact_email.trim() || null,
          contact_phone: form.contact_phone.trim() || null,
        },
      });
      setState({ status: 'ok', profile });
      setForm(contactForm(profile));
      setFormMessage({ kind: 'ok', text: 'Đã lưu thông tin liên hệ.' });
    } catch (error) {
      setFieldErrors(error.details?.fields ?? {});
      setFormMessage({ kind: 'error', text: error.message });
    } finally {
      setSaving(false);
    }
  }

  if (state.status === 'loading') {
    return <p role="status">Đang tải hồ sơ...</p>;
  }
  if (state.status === 'error') {
    return (
      <div role="alert" className="card">
        <p className="status-error">Không tải được hồ sơ: {state.message}</p>
        <button type="button" className="button" onClick={retry}>
          Thử lại
        </button>
      </div>
    );
  }

  const { profile } = state;
  const rows = [
    ['Mã sinh viên', profile.student_code],
    ['Họ tên', profile.full_name],
    ['Khóa', profile.cohort],
    ['Ngành', profile.program.name],
    ['Chương trình đào tạo', profile.program_version.name],
    ['Kỳ hiện tại', profile.current_semester?.name ?? NO_VALUE],
    ['Cố vấn', profile.advisors.join(', ') || 'Chưa phân công'],
  ];

  return (
    <>
      <section className="card">
        <h1>Hồ sơ</h1>
        <dl className="profile-list">
          {rows.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </section>
      <section className="card card--spaced">
        <h2>Thông tin liên hệ</h2>
        <form onSubmit={handleSubmit} noValidate>
          <ContactField
            id="contact-email"
            label="Email liên hệ"
            type="email"
            autoComplete="email"
            value={form.contact_email}
            errors={fieldErrors.contact_email}
            onChange={updateField('contact_email')}
          />
          <ContactField
            id="contact-phone"
            label="Số điện thoại"
            type="tel"
            autoComplete="tel"
            value={form.contact_phone}
            errors={fieldErrors.contact_phone}
            onChange={updateField('contact_phone')}
          />
          <p
            aria-live="polite"
            role="status"
            className={formMessage.kind === 'error' ? 'status-error' : 'status-ok'}
          >
            {formMessage.text}
          </p>
          <button type="submit" className="button" disabled={saving}>
            {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
          </button>
        </form>
      </section>
    </>
  );
}
