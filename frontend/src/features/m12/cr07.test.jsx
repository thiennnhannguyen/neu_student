import { screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, loggedInAs, renderApp, stubApi } from '../../test/fakeApi';
import { AI, BACKEND, m12Api, progressBody } from './testData';

const GOAL = 'Mục tiêu chính của bạn';
const DETAIL_API = 'GET /api/m12/progress/careers/slug/ai';
const MOCK_FOOTER =
  'Sản phẩm bài tập lớn – không phải hệ thống chính thức của Đại học Kinh tế Quốc dân.';

const cardLink = (name) =>
  screen
    .getAllByRole('link')
    .find((link) => link.querySelector('.career-card__name')?.textContent === name);

describe('CR-07: ngôi sao thay nhãn "Mục tiêu của bạn"', () => {
  it('danh sách nghề: chỉ thẻ nghề chính có ngôi sao, tên đọc được và tooltip; không còn nhãn chữ', async () => {
    m12Api();
    renderApp('/m12/dinh-huong');

    const star = await screen.findByRole('img', { name: GOAL });
    expect(star).toHaveAttribute('title', GOAL);
    expect(cardLink(AI.display_name)).toContainElement(star);
    expect(within(cardLink(BACKEND.display_name)).queryByRole('img', { name: GOAL })).toBeNull();
    expect(screen.getAllByRole('img', { name: GOAL })).toHaveLength(1);
    expect(screen.queryByText('Mục tiêu của bạn')).toBeNull();
  });

  it('trang nghề chính: đầu trang có ngôi sao, không có nút đặt mục tiêu', async () => {
    m12Api();
    renderApp('/m12/dinh-huong/nghe/ai');

    const hero = await screen.findByRole('region', { name: AI.display_name });
    expect(within(hero).getByRole('img', { name: GOAL })).toHaveAttribute('title', GOAL);
    expect(within(hero).queryByText('Mục tiêu của bạn')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Đặt làm mục tiêu chính' })).toBeNull();
  });

  it('nghề không phải mục tiêu chính: không có ngôi sao, vẫn có nút "Đặt làm mục tiêu chính"', async () => {
    m12Api('student', {
      [DETAIL_API]: () => jsonResponse(200, progressBody({ is_primary: false, fits_major: null })),
    });
    renderApp('/m12/dinh-huong/nghe/ai');

    const hero = await screen.findByRole('region', { name: AI.display_name });
    expect(within(hero).queryByRole('img', { name: GOAL })).toBeNull();
    expect(screen.getByRole('button', { name: 'Đặt làm mục tiêu chính' })).toBeInTheDocument();
  });
});

describe('CR-07: bỏ hàng chú giải trạng thái ở Hướng nghiệp', () => {
  it.each(['roadmap', 'courses', 'skills'])('tab %s không có hàng chú giải', async (tab) => {
    m12Api();
    renderApp(`/m12/dinh-huong/nghe/ai?tab=${tab}`);

    await screen.findByRole('region', { name: AI.display_name });
    await screen.findByRole('tabpanel');
    expect(screen.queryByRole('list', { name: 'Chú giải trạng thái' })).toBeNull();
  });
});

describe('CR-07: bỏ badge "Dữ liệu mẫu", giữ dòng không phải hệ thống chính thức', () => {
  it('trang đăng nhập', async () => {
    stubApi({
      'GET /api/auth/me': () => apiError(401, 'UNAUTHENTICATED', 'Bạn chưa đăng nhập.'),
      'GET /api/health': () => jsonResponse(200, { status: 'ok' }),
    });
    renderApp('/login');

    await screen.findByLabelText('Mật khẩu');
    expect(screen.queryByText('Dữ liệu mẫu')).toBeNull();
    expect(screen.getByText(MOCK_FOOTER)).toBeInTheDocument();
  });

  it.each(['student', 'advisor', 'admin', 'support_staff'])(
    '%s: thanh trên cùng không còn badge, trang vẫn có dòng chân trang',
    async (role) => {
      loggedInAs(role);
      renderApp('/');

      const banner = await screen.findByRole('banner');
      await waitFor(() => expect(screen.getByText(MOCK_FOOTER)).toBeInTheDocument());
      expect(within(banner).queryByText('Dữ liệu mẫu')).toBeNull();
      expect(screen.queryByText('Dữ liệu mẫu')).toBeNull();
    },
  );
});
