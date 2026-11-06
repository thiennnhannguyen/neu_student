import { Target } from 'lucide-react';
import { useState } from 'react';
import { apiRequest } from '../../api/client';
import { Button, ConfirmDialog, useToast } from '../../components/ui';

/** Chỉ sinh viên thấy nút này; nơi gọi tự kiểm tra vai trò. Phía server cũng chỉ cho sinh viên. */
export default function SetGoalButton({ career, onChanged, label = 'Đặt làm mục tiêu chính' }) {
  const { show } = useToast();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function confirm() {
    setBusy(true);
    setError('');
    try {
      await apiRequest('/api/m12/career-goal', {
        method: 'PUT',
        body: { career_id: career.id },
      });
      setOpen(false);
      show(`Đã đặt ${career.name} làm mục tiêu chính.`);
      onChanged();
    } catch (cause) {
      setError(cause.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Button
        variant="secondary"
        iconLeft={Target}
        onClick={() => {
          setError('');
          setOpen(true);
        }}
      >
        {label}
      </Button>
      {open && (
        <ConfirmDialog
          title="Đặt làm mục tiêu chính?"
          confirmLabel="Xác nhận"
          busy={busy}
          error={error}
          onConfirm={confirm}
          onCancel={() => setOpen(false)}
        >
          <p>
            {career.name} sẽ trở thành nghề chính của bạn. Lịch sử học tập và tiến độ không bị mất.
          </p>
        </ConfirmDialog>
      )}
    </>
  );
}
