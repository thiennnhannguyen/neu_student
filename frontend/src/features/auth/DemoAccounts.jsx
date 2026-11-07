import { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';

const ROLE_LABELS = {
  student: 'Sinh viên',
  advisor: 'Cố vấn',
  admin: 'Quản trị',
  support_staff: 'Hỗ trợ',
};

/**
 * Chỉ hiện khi chạy profile demo-k68: API trả danh sách rỗng ở profile test và 404 ở production,
 * nên D-136 vẫn đúng với dữ liệu test. Không có mật khẩu trong mã giao diện.
 */
export default function DemoAccounts({ onPick }) {
  const [accounts, setAccounts] = useState([]);

  useEffect(() => {
    const controller = new AbortController();
    apiRequest('/api/auth/demo-accounts', { signal: controller.signal })
      .then((data) => setAccounts(data.accounts))
      .catch(() => setAccounts([]));
    return () => controller.abort();
  }, []);

  if (accounts.length === 0) {
    return null;
  }
  return (
    <section className="demo-accounts" aria-labelledby="demo-accounts-title">
      <h2 id="demo-accounts-title">Tài khoản demo</h2>
      <p>Bấm để điền tên đăng nhập. Mật khẩu xem trong README.</p>
      <ul>
        {accounts.map((account) => (
          <li key={account.username}>
            <button type="button" onClick={() => onPick(account.username)}>
              {account.username}
              <span>{ROLE_LABELS[account.role]}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
