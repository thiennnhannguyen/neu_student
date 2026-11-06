import { Pencil, Save } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import {
  Avatar,
  Button,
  Card,
  ErrorState,
  FormField,
  Input,
  PageHeader,
  Skeleton,
  useToast,
} from '../../components/ui';

const NO_VALUE = 'Chưa có';
const NOT_SET = 'Chưa cập nhật';

function contactForm(profile) {
  return {
    contact_email: profile.contact_email ?? '',
    contact_phone: profile.contact_phone ?? '',
  };
}

function IdentityCard({ profile }) {
  const rows = [
    ['Mã sinh viên', profile.student_code],
    ['Khóa', profile.cohort],
    ['Ngành', profile.program.name],
    ['Chương trình đào tạo', profile.program_version.name],
    ['Kỳ hiện tại', profile.current_semester?.name ?? NO_VALUE],
    ['Cố vấn', profile.advisors.join(', ') || 'Chưa phân công'],
  ];
  return (
    <Card className="span-5">
      <div className="identity">
        <Avatar name={profile.full_name} size="lg" />
        <h2 className="identity__name">{profile.full_name}</h2>
      </div>
      <dl className="detail-list">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}

function ContactCard({ profile, onSaved }) {
  const { show } = useToast();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(() => contactForm(profile));
  const [saving, setSaving] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState('');

  function updateField(name) {
    return (event) => setForm((current) => ({ ...current, [name]: event.target.value }));
  }

  function startEditing() {
    setForm(contactForm(profile));
    setFieldErrors({});
    setFormError('');
    setEditing(true);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setFieldErrors({});
    setFormError('');
    setSaving(true);
    try {
      const saved = await apiRequest('/api/students/me/contact', {
        method: 'PATCH',
        body: {
          contact_email: form.contact_email.trim() || null,
          contact_phone: form.contact_phone.trim() || null,
        },
      });
      onSaved(saved);
      setEditing(false);
      show('Đã lưu thông tin liên hệ.');
    } catch (error) {
      setFieldErrors(error.details?.fields ?? {});
      setFormError(error.message);
    } finally {
      setSaving(false);
    }
  }

  if (!editing) {
    return (
      <Card
        className="span-7"
        title="Thông tin liên hệ"
        actions={
          <Button variant="secondary" size="sm" iconLeft={Pencil} onClick={startEditing}>
            Sửa
          </Button>
        }
      >
        <dl className="detail-list">
          <div>
            <dt>Email liên hệ</dt>
            <dd>{profile.contact_email ?? NOT_SET}</dd>
          </div>
          <div>
            <dt>Số điện thoại</dt>
            <dd>{profile.contact_phone ?? NOT_SET}</dd>
          </div>
        </dl>
      </Card>
    );
  }

  return (
    <Card className="span-7" title="Thông tin liên hệ">
      <form onSubmit={handleSubmit} noValidate>
        <FormField id="contact-email" label="Email liên hệ" errors={fieldErrors.contact_email}>
          <Input
            type="email"
            autoComplete="email"
            value={form.contact_email}
            onChange={updateField('contact_email')}
          />
        </FormField>
        <FormField id="contact-phone" label="Số điện thoại" errors={fieldErrors.contact_phone}>
          <Input
            type="tel"
            autoComplete="tel"
            value={form.contact_phone}
            onChange={updateField('contact_phone')}
          />
        </FormField>
        {formError && (
          <p role="alert" className="status-error">
            {formError}
          </p>
        )}
        <div className="form-actions">
          <Button type="submit" iconLeft={Save} loading={saving}>
            {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
          </Button>
          <Button variant="ghost" disabled={saving} onClick={() => setEditing(false)}>
            Hủy
          </Button>
        </div>
      </form>
    </Card>
  );
}

export default function ProfilePage() {
  const [state, setState] = useState({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    apiRequest('/api/students/me', { signal: controller.signal })
      .then((profile) => setState({ status: 'ok', profile }))
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

  const header = (
    <PageHeader title="Hồ sơ" description="Thông tin học tập và cách liên hệ với bạn." />
  );
  if (state.status === 'loading') {
    return (
      <>
        {header}
        <p role="status" className="visually-hidden">
          Đang tải hồ sơ...
        </p>
        <div className="grid-12">
          <Card className="span-5">
            <Skeleton height={120} />
          </Card>
          <Card className="span-7">
            <Skeleton height={120} />
          </Card>
        </div>
      </>
    );
  }
  if (state.status === 'error') {
    return (
      <>
        {header}
        <ErrorState title="Không tải được hồ sơ" description={state.message} onRetry={retry} />
      </>
    );
  }
  return (
    <>
      {header}
      <div className="grid-12">
        <IdentityCard profile={state.profile} />
        <ContactCard
          profile={state.profile}
          onSaved={(profile) => setState({ status: 'ok', profile })}
        />
      </div>
    </>
  );
}
