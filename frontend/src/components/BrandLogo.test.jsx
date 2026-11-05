import { existsSync } from 'node:fs';
import { join } from 'node:path';
import process from 'node:process';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { IMAGES } from '../constants/images';
import BrandLogo from './BrandLogo';

describe('BrandLogo', () => {
  it('hiện ảnh logo khi chưa có lỗi', () => {
    render(<BrandLogo />);

    expect(screen.getByRole('img')).toHaveAttribute('src', '/images/brand/logo_neu.svg');
    expect(screen.queryByText('NEU')).not.toBeInTheDocument();
  });

  it('tải logo lỗi thì hiện chữ NEU, không còn ảnh hỏng', () => {
    render(<BrandLogo />);

    fireEvent.error(screen.getByRole('img'));

    expect(screen.getByText('NEU')).toBeInTheDocument();
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  it('logo trang trí có alt rỗng và không vào cây trợ năng', () => {
    const { container } = render(<BrandLogo decorative className="x" />);

    const image = container.querySelector('img');
    expect(image).toHaveAttribute('alt', '');
    expect(image).toHaveClass('x');
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  it('logo trang trí tải lỗi thì ẩn, không hiện chữ NEU', () => {
    const { container } = render(<BrandLogo decorative />);

    fireEvent.error(container.querySelector('img'));

    expect(container).toBeEmptyDOMElement();
  });

  it.each(Object.entries(IMAGES))('tệp ảnh %s có trong public', (_name, path) => {
    expect(existsSync(join(process.cwd(), 'public', path))).toBe(true);
  });
});
