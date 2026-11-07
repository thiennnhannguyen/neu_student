import {
  BellRing,
  BookOpen,
  ChartLine,
  ClipboardList,
  Compass,
  History,
  LayoutDashboard,
  LifeBuoy,
  ShieldAlert,
  UserRound,
  CalendarRange,
} from 'lucide-react';

const STUDENT = 'student';
const ADVISOR = 'advisor';
const SUPPORT_STAFF = 'support_staff';
const ADMIN = 'admin';

export const ROLE_LABELS = {
  [STUDENT]: 'Sinh viên',
  [ADVISOR]: 'Cố vấn',
  [SUPPORT_STAFF]: 'Nhân sự hỗ trợ',
  [ADMIN]: 'Quản trị',
};

export const M11_READERS = [STUDENT, ADVISOR, ADMIN];

/**
 * `implemented: true` là trang đã làm; còn lại hiện "Đang phát triển", `phase` là giai đoạn dự kiến.
 * `inSidebar: false` là trang có route nhưng nằm ở menu người dùng.
 * `nested: true` là trang có trang con; mở trang con thì mục này vẫn sáng ở sidebar.
 * `title` hiện ở sidebar, `crumb` hiện ở đường dẫn phân cấp; `id` giữ tên nội bộ của module.
 */
export const MENU_GROUPS = [
  {
    id: 'chung',
    title: null,
    items: [
      {
        label: 'Tổng quan',
        path: '/',
        icon: LayoutDashboard,
        roles: [STUDENT, ADVISOR, SUPPORT_STAFF, ADMIN],
        implemented: true,
      },
      {
        label: 'Hồ sơ',
        path: '/ho-so',
        icon: UserRound,
        roles: [STUDENT],
        implemented: true,
        inSidebar: false,
      },
    ],
  },
  {
    id: 'm11',
    title: 'HỌC TẬP',
    crumb: 'Học tập',
    items: [
      {
        label: 'Kết quả',
        path: '/m11/ket-qua',
        icon: ClipboardList,
        roles: M11_READERS,
        implemented: true,
      },
      {
        label: 'Phân tích',
        path: '/m11/phan-tich',
        icon: ChartLine,
        roles: M11_READERS,
        implemented: true,
      },
      {
        label: 'Cảnh báo',
        path: '/m11/canh-bao',
        icon: ShieldAlert,
        roles: M11_READERS,
        implemented: true,
      },
    ],
  },
  {
    id: 'm12',
    title: 'ĐỊNH HƯỚNG & HỖ TRỢ',
    crumb: 'Định hướng & hỗ trợ',
    items: [
      {
        label: 'Định hướng nghề',
        path: '/m12/dinh-huong',
        icon: Compass,
        roles: M11_READERS,
        implemented: true,
        nested: true,
      },
      {
        label: 'Kế hoạch học tập',
        path: '/m12/ke-hoach',
        icon: CalendarRange,
        roles: [STUDENT, ADVISOR],
        phase: '09',
      },
      {
        label: 'Học liệu',
        path: '/m12/hoc-lieu',
        icon: BookOpen,
        roles: [STUDENT, ADVISOR, SUPPORT_STAFF, ADMIN],
        phase: '10',
      },
      {
        label: 'Yêu cầu hỗ trợ',
        path: '/m12/yeu-cau-ho-tro',
        icon: LifeBuoy,
        roles: [STUDENT, ADVISOR, SUPPORT_STAFF, ADMIN],
        phase: '10',
      },
      { label: 'Nhắc nhở', path: '/m12/nhac-nho', icon: BellRing, roles: [STUDENT], phase: '10' },
      // Giai đoạn 10: { label: 'Duyệt minh chứng', roles: [ADVISOR] }
      // M12-15 giao diện (P1): { label: 'Quản trị nghề', roles: [ADMIN] }
    ],
  },
  {
    id: 'quan-tri',
    title: 'QUẢN TRỊ',
    crumb: 'Quản trị',
    items: [
      {
        label: 'Nhật ký',
        path: '/quan-tri/nhat-ky',
        icon: History,
        roles: [ADMIN],
        implemented: true,
      },
    ],
  },
];

export function menuForRole(role) {
  return MENU_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => item.roles.includes(role) && item.inSidebar !== false),
  })).filter((group) => group.items.length > 0);
}

export const PENDING_ITEMS = MENU_GROUPS.flatMap((group) => group.items).filter(
  (item) => !item.implemented,
);

const CAREER_ROOT = '/m12/dinh-huong';
const CAREER_SUBPAGES = [
  { prefix: `${CAREER_ROOT}/tat-ca`, label: 'Tất cả nghề' },
  { prefix: `${CAREER_ROOT}/nghe/`, label: 'Chi tiết nghề' },
];

function careerSubpageMeta(pathname) {
  const sub = CAREER_SUBPAGES.find((entry) => pathname.startsWith(entry.prefix));
  if (!sub) {
    return null;
  }
  return {
    title: sub.label,
    trail: [
      { label: 'Tổng quan', to: '/' },
      { label: 'Định hướng & hỗ trợ' },
      { label: 'Định hướng nghề', to: CAREER_ROOT },
      { label: sub.label },
    ],
  };
}

/** Tiêu đề và đường dẫn phân cấp của trang đang mở. Trang không có trong menu trả null. */
export function pageMetaFor(pathname) {
  const subpage = careerSubpageMeta(pathname);
  if (subpage) {
    return subpage;
  }
  for (const group of MENU_GROUPS) {
    const item = group.items.find((entry) => entry.path === pathname);
    if (item) {
      const trail = [
        ...(item.path === '/' ? [] : [{ label: 'Tổng quan', to: '/' }]),
        ...(group.crumb ? [{ label: group.crumb }] : []),
        { label: item.label },
      ];
      return { title: item.label, trail };
    }
  }
  return null;
}
