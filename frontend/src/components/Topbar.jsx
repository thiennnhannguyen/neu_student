import { Menu } from 'lucide-react';
import { useState } from 'react';
import { useLocation } from 'react-router';
import ScopeChip from '../features/m11/ScopeChip';
import StudentPicker from '../features/m11/StudentPicker';
import useStudentOptions from '../features/m11/useStudentOptions';
import { carrySearch } from '../features/m11/scopeQuery';
import { pageMetaFor } from './menu';
import { useCurrentPageLabel } from './PageLabelContext';
import { Breadcrumb } from './ui/PageHeader';
import NotificationBell from '../features/notifications/NotificationBell';
import UserMenu from './UserMenu';

/**
 * Phản hồi CR-11 (B3, bổ sung D-309): trang LMS Demo có ô chọn sinh viên riêng (theo phạm vi gửi
 * dữ liệu), nên ẩn ô chọn sinh viên của thanh trên cùng để không có hai ô cùng tên.
 */
const PAGES_WITHOUT_STUDENT_PICKER = ['/quan-tri/lms-demo'];

/** Thanh trên cùng chỉ có đường dẫn phân cấp; tiêu đề trang là h1 duy nhất, nằm trong trang. */
export default function Topbar({ menuOpen, onToggleMenu }) {
  const { pathname, search } = useLocation();
  const pageLabel = useCurrentPageLabel();
  const [logoutError, setLogoutError] = useState('');
  const students = useStudentOptions();
  const meta = pageMetaFor(pathname);
  // keepScope: liên kết giữ ?student= (và kỳ); current: nhãn cuối thay bằng nhãn trang báo lên.
  const trail = meta?.trail.map((item) => ({
    ...item,
    to: item.to && item.keepScope ? `${item.to}${carrySearch(search)}` : item.to,
    label: item.current && pageLabel ? pageLabel : item.label,
  }));
  const ownPicker = PAGES_WITHOUT_STUDENT_PICKER.includes(pathname);
  const error = logoutError || (students.failed ? 'Không tải được danh sách sinh viên.' : '');

  return (
    <header className="topbar">
      <button
        type="button"
        className="icon-button topbar__menu"
        aria-label="Menu"
        aria-expanded={menuOpen}
        aria-controls="app-sidebar"
        onClick={onToggleMenu}
      >
        <Menu size={22} aria-hidden="true" />
      </button>
      <div className="topbar__crumbs">
        {meta ? (
          trail.length > 1 && <Breadcrumb items={trail} />
        ) : (
          <p className="topbar__product">NEU Student</p>
        )}
      </div>
      <div className="topbar__tools">
        {students.enabled && !ownPicker && <StudentPicker students={students} />}
        {!ownPicker && <ScopeChip students={students} />}
        <NotificationBell />
        <UserMenu onLogoutError={setLogoutError} />
      </div>
      {error && (
        <p role="alert" className="status-error topbar__error">
          {error}
        </p>
      )}
    </header>
  );
}
