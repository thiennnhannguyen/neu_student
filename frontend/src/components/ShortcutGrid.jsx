import { ArrowRight } from 'lucide-react';
import { Link, useLocation } from 'react-router';
import { carrySearch } from '../features/m11/scopeQuery';
import { MENU_GROUPS } from './menu';

const NOTES = {
  '/m11/ket-qua': 'Xem bảng điểm và lịch sử học lại',
  '/m11/phan-tich': 'Xu hướng GPA, tín chỉ, đối chiếu chương trình',
  '/m12/dinh-huong': 'Tìm hiểu nghề và kỹ năng cần có',
  '/m12/yeu-cau-ho-tro': 'Gửi và theo dõi yêu cầu hỗ trợ',
  '/m12/hoc-lieu': 'Tài liệu học tập theo học phần',
};

export default function ShortcutGrid({ paths }) {
  const { search } = useLocation();
  const items = MENU_GROUPS.flatMap((group) => group.items);
  return (
    <section aria-labelledby="shortcut-title" className="shortcuts">
      <h2 id="shortcut-title" className="section-heading">
        Lối tắt
      </h2>
      <div className="grid-12">
        {paths.map((path) => {
          const item = items.find((entry) => entry.path === path);
          const Icon = item.icon;
          return (
            <Link key={path} to={`${path}${carrySearch(search)}`} className="shortcut span-3">
              <span className="shortcut__icon">
                <Icon size={20} aria-hidden="true" />
              </span>
              <span className="shortcut__text">
                <strong>{item.label}</strong>
                <span>{NOTES[path]}</span>
              </span>
              <ArrowRight size={16} aria-hidden="true" className="shortcut__arrow" />
            </Link>
          );
        })}
      </div>
    </section>
  );
}
