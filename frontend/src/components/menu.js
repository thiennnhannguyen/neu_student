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

/** `implemented: true` là trang đã làm; còn lại hiện "Đang phát triển". */
export const MENU_GROUPS = [
  {
    title: null,
    items: [
      {
        label: 'Tổng quan',
        path: '/',
        roles: [STUDENT, ADVISOR, SUPPORT_STAFF, ADMIN],
        implemented: true,
      },
      { label: 'Hồ sơ', path: '/ho-so', roles: [STUDENT], implemented: true },
    ],
  },
  {
    title: 'M11',
    items: [
      { label: 'Kết quả', path: '/m11/ket-qua', roles: [STUDENT, ADVISOR, ADMIN] },
      { label: 'Phân tích', path: '/m11/phan-tich', roles: [STUDENT, ADVISOR, ADMIN] },
      { label: 'Cảnh báo', path: '/m11/canh-bao', roles: [STUDENT, ADVISOR, ADMIN] },
    ],
  },
  {
    title: 'M12',
    items: [
      { label: 'Định hướng nghề', path: '/m12/dinh-huong', roles: [STUDENT, ADVISOR, ADMIN] },
      { label: 'Kế hoạch học tập', path: '/m12/ke-hoach', roles: [STUDENT, ADVISOR] },
      { label: 'Học liệu', path: '/m12/hoc-lieu', roles: [STUDENT, ADVISOR, SUPPORT_STAFF, ADMIN] },
      {
        label: 'Yêu cầu hỗ trợ',
        path: '/m12/yeu-cau-ho-tro',
        roles: [STUDENT, ADVISOR, SUPPORT_STAFF, ADMIN],
      },
      { label: 'Nhắc nhở', path: '/m12/nhac-nho', roles: [STUDENT] },
      // Giai đoạn 10: { label: 'Duyệt minh chứng', roles: [ADVISOR] }
      // M12-15 giao diện (P1): { label: 'Quản trị nghề', roles: [ADMIN] }
    ],
  },
  {
    title: 'Quản trị',
    items: [{ label: 'Nhật ký', path: '/quan-tri/nhat-ky', roles: [ADMIN], implemented: true }],
  },
];

export function menuForRole(role) {
  return MENU_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => item.roles.includes(role)),
  })).filter((group) => group.items.length > 0);
}

export const PENDING_ITEMS = MENU_GROUPS.flatMap((group) => group.items).filter(
  (item) => !item.implemented,
);
