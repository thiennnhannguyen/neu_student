import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, loggedInAs, pendingResponse, renderApp } from '../../test/fakeApi';

const PROFILE = {
  id: 'SV01',
  student_code: 'SV01',
  full_name: 'Sinh viên 1 (mẫu)',
  cohort: 'K66',
  program: { id: 'prog', name: 'Công nghệ thông tin (mẫu)' },
  program_version: { id: 'pv', name: 'CTĐT K66 (mẫu)', version: 1 },
  current_semester: { id: 'S5', name: 'Học kỳ 5 (mẫu)' },
  advisors: ['Cố vấn 1 (mẫu)'],
  contact_email: 'sv01@example.test',
  contact_phone: '0900000001',
  is_mock: true,
};

function profileApi(extra = {}) {
  return loggedInAs('student', {
    'GET /api/students/me': () => jsonResponse(200, PROFILE),
    ...extra,
  });
}

describe('trang Hồ sơ', () => {
  it('hiện đang tải rồi đủ thông tin', async () => {
    const profile = pendingResponse();
    profileApi({ 'GET /api/students/me': profile.handler });

    renderApp('/ho-so');

    expect(await screen.findByText('Đang tải hồ sơ...')).toBeInTheDocument();
    profile.resolve(jsonResponse(200, PROFILE));
    expect(await screen.findByRole('heading', { name: 'Hồ sơ' })).toBeInTheDocument();
    for (const text of [
      'SV01',
      'K66',
      'Công nghệ thông tin (mẫu)',
      'CTĐT K66 (mẫu)',
      'Học kỳ 5 (mẫu)',
      'Cố vấn 1 (mẫu)',
    ]) {
      expect(screen.getByText(text)).toBeInTheDocument();
    }
    expect(screen.getByLabelText('Email liên hệ')).toHaveValue('sv01@example.test');
    expect(screen.getByLabelText('Số điện thoại')).toHaveValue('0900000001');
  });

  it('dữ liệu rỗng hiện chữ thay thế', async () => {
    profileApi({
      'GET /api/students/me': () =>
        jsonResponse(200, {
          ...PROFILE,
          current_semester: null,
          advisors: [],
          contact_email: null,
          contact_phone: null,
        }),
    });

    renderApp('/ho-so');

    expect(await screen.findByText('Chưa có')).toBeInTheDocument();
    expect(screen.getByText('Chưa phân công')).toBeInTheDocument();
    expect(screen.getByLabelText('Email liên hệ')).toHaveValue('');
  });

  it('lỗi tải thì hiện lỗi và thử lại được', async () => {
    let calls = 0;
    profileApi({
      'GET /api/students/me': () => {
        calls += 1;
        return calls === 1
          ? apiError(500, 'INTERNAL_ERROR', 'Hệ thống gặp lỗi.')
          : jsonResponse(200, PROFILE);
      },
    });
    const user = userEvent.setup();

    renderApp('/ho-so');

    expect(await screen.findByRole('alert')).toHaveTextContent('Hệ thống gặp lỗi.');
    await user.click(screen.getByRole('button', { name: 'Thử lại' }));
    expect(await screen.findByRole('heading', { name: 'Hồ sơ' })).toBeInTheDocument();
  });

  it('lưu thành công: gửi đúng 2 trường và hiện thông báo', async () => {
    let sent;
    profileApi({
      'PATCH /api/students/me/contact': (_url, options) => {
        sent = JSON.parse(options.body);
        return jsonResponse(200, { ...PROFILE, contact_phone: '0912345678' });
      },
    });
    const user = userEvent.setup();

    renderApp('/ho-so');
    const phone = await screen.findByLabelText('Số điện thoại');
    await user.clear(phone);
    await user.type(phone, ' 0912345678 ');
    await user.click(screen.getByRole('button', { name: 'Lưu thay đổi' }));

    expect(await screen.findByText('Đã lưu thông tin liên hệ.')).toHaveAttribute(
      'aria-live',
      'polite',
    );
    expect(sent).toEqual({ contact_email: 'sv01@example.test', contact_phone: '0912345678' });
    expect(phone).toHaveValue('0912345678');
  });

  it('xóa trắng ô thì gửi null', async () => {
    let sent;
    profileApi({
      'PATCH /api/students/me/contact': (_url, options) => {
        sent = JSON.parse(options.body);
        return jsonResponse(200, { ...PROFILE, contact_email: null });
      },
    });
    const user = userEvent.setup();

    renderApp('/ho-so');
    await user.clear(await screen.findByLabelText('Email liên hệ'));
    await user.click(screen.getByRole('button', { name: 'Lưu thay đổi' }));

    await screen.findByText('Đã lưu thông tin liên hệ.');
    expect(sent.contact_email).toBeNull();
  });

  it('lỗi 422 hiện cạnh đúng ô và gắn aria', async () => {
    profileApi({
      'PATCH /api/students/me/contact': () =>
        apiError(422, 'VALIDATION_ERROR', 'Dữ liệu không hợp lệ.', {
          fields: { contact_email: ['Email không hợp lệ.'] },
        }),
    });
    const user = userEvent.setup();

    renderApp('/ho-so');
    await user.click(await screen.findByRole('button', { name: 'Lưu thay đổi' }));

    const message = await screen.findByText('Email không hợp lệ.');
    const email = screen.getByLabelText('Email liên hệ');
    expect(email).toHaveAttribute('aria-invalid', 'true');
    expect(email).toHaveAttribute('aria-describedby', message.id);
    expect(screen.getByLabelText('Số điện thoại')).not.toHaveAttribute('aria-invalid');
    expect(screen.getByRole('button', { name: 'Lưu thay đổi' })).toBeEnabled();
  });

  it('dùng được bằng bàn phím: Enter trong ô để lưu', async () => {
    let calls = 0;
    profileApi({
      'PATCH /api/students/me/contact': () => {
        calls += 1;
        return jsonResponse(200, PROFILE);
      },
    });
    const user = userEvent.setup();

    renderApp('/ho-so');
    (await screen.findByLabelText('Email liên hệ')).focus();
    await user.tab();
    expect(screen.getByLabelText('Số điện thoại')).toHaveFocus();
    await user.keyboard('{Enter}');

    await screen.findByText('Đã lưu thông tin liên hệ.');
    expect(calls).toBe(1);
  });
});
