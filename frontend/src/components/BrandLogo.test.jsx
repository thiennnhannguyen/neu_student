import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import BrandLogo from './BrandLogo';

describe('BrandLogo', () => {
  it('hiện ảnh logo khi chưa có lỗi', () => {
    render(<BrandLogo />);

    expect(screen.getByRole('img')).toHaveAttribute('src', '/brand/logo.svg');
    expect(screen.queryByText('NEU')).not.toBeInTheDocument();
  });

  it('tải logo lỗi thì hiện chữ NEU, không còn ảnh hỏng', () => {
    render(<BrandLogo />);

    fireEvent.error(screen.getByRole('img'));

    expect(screen.getByText('NEU')).toBeInTheDocument();
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });
});
