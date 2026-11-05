const DEMO_PASSWORD = 'Demo@12345';
const DEMO_ACCOUNTS = [
  { username: 'sv01', role: 'Sinh viên' },
  { username: 'sv07', role: 'Sinh viên' },
  { username: 'gv1', role: 'Cố vấn' },
  { username: 'ht1', role: 'Nhân sự hỗ trợ' },
  { username: 'admin', role: 'Quản trị' },
];

export default function DemoAccounts({ onPick }) {
  return (
    <details className="demo-box">
      <summary>Tài khoản demo (dữ liệu mẫu)</summary>
      <p className="demo-box__password">
        Mật khẩu demo: <code>{DEMO_PASSWORD}</code>
      </p>
      <ul className="demo-box__list">
        {DEMO_ACCOUNTS.map(({ username, role }) => (
          <li key={username}>
            <button type="button" className="demo-box__account" onClick={() => onPick(username)}>
              <strong>{username}</strong> · {role}
            </button>
          </li>
        ))}
      </ul>
    </details>
  );
}
