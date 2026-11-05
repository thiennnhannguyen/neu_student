import { useState } from 'react';
import { IMAGES } from '../constants/images';

/**
 * Logo NEU. Tải lỗi thì hiện chữ "NEU", không hiện ảnh hỏng.
 * `decorative`: logo lặp lại chỉ để trang trí, nên không đọc cho trình đọc màn hình và lỗi thì ẩn.
 */
export default function BrandLogo({ decorative = false, className = 'app-header__logo' }) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return decorative ? null : <span className="brand-fallback">NEU</span>;
  }
  return (
    <img
      className={className}
      src={IMAGES.logoNeu}
      alt={decorative ? '' : 'Logo Đại học Kinh tế Quốc dân'}
      onError={() => setFailed(true)}
    />
  );
}
