/** D-326: mọi dấu tick xanh dùng chung icon tròn xanh lá đặc, dấu tick trắng. */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { ReviewedQuestions } from '../../features/m12/framework/QuizResult';
import { QuizMark } from '../../features/m12/CareerProjects';
import TicketStatus from '../../features/m12/support/TicketStatus';
import CheckBadge from './CheckBadge';
import StatusChip, { StatusLegend } from './StatusChip';
import { ToastProvider, useToast } from './Toast';

function badgeIn(element) {
  return element.querySelector('svg.check-badge');
}

describe('Icon tick tròn xanh (D-326)', () => {
  it('hình tròn đặc màu token, dấu tick trắng', () => {
    const { container } = render(<CheckBadge size={20} aria-hidden="true" />);
    const svg = badgeIn(container);
    expect(svg).toHaveAttribute('width', '20');
    expect(svg.querySelector('circle')).toHaveAttribute('fill', 'var(--check-badge-bg)');
    expect(svg.querySelector('path')).toHaveAttribute('stroke', 'var(--neu-white)');
    expect(container.querySelector('.lucide')).toBeNull();
  });

  it('Đạt, Đạt qua tương đương, Đã chấm và chú giải dùng icon mới; trạng thái khác giữ icon cũ', () => {
    for (const status of ['done', 'done_via_equivalency', 'lms_graded']) {
      const { container, unmount } = render(<StatusChip status={status} />);
      expect(badgeIn(container), status).not.toBeNull();
      unmount();
    }
    const { container } = render(<StatusChip status="failed" />);
    expect(badgeIn(container)).toBeNull();
    const legend = render(<StatusLegend statuses={['done', 'not_started']} />);
    expect(legend.container.querySelectorAll('svg.check-badge')).toHaveLength(1);
  });

  it('Checklist Đã đạt, Đáp án đúng, yêu cầu Hoàn thành dùng icon mới', () => {
    const done = render(<QuizMark done />);
    expect(badgeIn(screen.getByRole('img', { name: 'Đã đạt' }))).not.toBeNull();
    done.unmount();
    render(<QuizMark done={false} />);
    expect(document.querySelector('svg.check-badge')).toBeNull();

    render(
      <ReviewedQuestions
        questions={[
          {
            id: 'q1',
            prompt: 'Câu hỏi',
            explanation: 'Vì đúng.',
            selected_option_ids: [],
            options: [
              { id: 'a', text: 'Đúng', is_correct: true },
              { id: 'b', text: 'Sai', is_correct: false },
            ],
          },
        ]}
      />,
    );
    const right = screen.getByRole('img', { name: 'Đáp án đúng' });
    expect(right).toHaveClass('check-badge');

    const ticket = render(<TicketStatus status="done" />);
    expect(badgeIn(ticket.container)).not.toBeNull();
  });

  it('thông báo thành công dùng icon mới, thông báo lỗi giữ icon lỗi', async () => {
    function Host() {
      const { show } = useToast();
      return (
        <>
          <button type="button" onClick={() => show('Đã lưu')}>
            Ok
          </button>
          <button type="button" onClick={() => show('Hỏng', 'error')}>
            Lỗi
          </button>
        </>
      );
    }
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <Host />
      </ToastProvider>,
    );
    await user.click(screen.getByRole('button', { name: 'Ok' }));
    expect(badgeIn(document.querySelector('.toast--success'))).not.toBeNull();
    await user.click(screen.getByRole('button', { name: 'Lỗi' }));
    expect(badgeIn(document.querySelector('.toast--error'))).toBeNull();
  });
});
