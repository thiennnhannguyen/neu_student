/** CR-13b (D-315): một bộ từ chỉ mức Ổn / Cần chú ý / Nguy cơ cao cho Cảnh báo học vụ và môn học. */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { StatusChip } from '../../components/ui';
import { STATUS_CHIPS } from '../../components/ui/StatusChip';
import { jsonResponse, renderApp } from '../../test/fakeApi';
import { LEVELS } from './prediction';
import { RISKS, m11Api } from './testData';

const WARNING_NOTE =
  'Mức cảnh báo tính từ chuyên cần, bài tập và báo cáo tuần, nên một môn có thể có điểm dự kiến khá nhưng vẫn bị cảnh báo.';

describe('bộ từ chỉ mức thống nhất (D-315)', () => {
  it('Cảnh báo học vụ dùng đúng chữ và icon của mức môn học', () => {
    expect(STATUS_CHIPS.normal.label).toBe('Ổn');
    expect(STATUS_CHIPS.normal.label).toBe(LEVELS.ok.label);
    expect(STATUS_CHIPS.watch.label).toBe(LEVELS.watch.label);
    expect(STATUS_CHIPS.warning.label).toBe(LEVELS.high.label);
    expect(STATUS_CHIPS.watch.icon).toBe(LEVELS.watch.icon);
    expect(STATUS_CHIPS.warning.icon).toBe(LEVELS.high.icon);
    for (const level of ['normal', 'watch', 'warning']) {
      const { unmount } = render(<StatusChip status={level} />);
      expect(screen.queryByText(/^(Bình thường|Chú ý|Cảnh báo)$/)).toBeNull();
      unmount();
    }
  });

  it('khối Cảnh báo học vụ: tên ngưỡng mới, không còn "Ngưỡng chú ý", "Ngưỡng cảnh báo"', async () => {
    m11Api('student', {
      'GET /api/m11/risks': () => jsonResponse(200, { ...RISKS, overall: 'watch' }),
    });
    renderApp('/m11/phan-tich');
    const block = (await screen.findByRole('heading', { name: 'Cảnh báo học vụ' })).parentElement;
    await within(block).findAllByText('Ngưỡng Cần chú ý');
    expect(within(block).getAllByText('Ngưỡng Nguy cơ cao').length).toBeGreaterThan(0);
    expect(within(block).queryByText(/^Ngưỡng (chú ý|cảnh báo)$/)).toBeNull();
    expect(within(block).getAllByText('Cần chú ý').length).toBeGreaterThan(0);
  });
});

describe('ⓘ cạnh "Điểm dự kiến" có câu về mức cảnh báo', () => {
  const glossary = {
    items: ['course_prediction', 'course_warning', 'prediction_range'].map((key) => ({
      key,
      name: key,
      formula: 'f',
      source: 's',
      note: `${WARNING_NOTE} Ghi chú khác.`,
      rule_version: null,
      scope: null,
      scope_label: null,
    })),
  };

  it('ở bảng môn đang học', async () => {
    const user = userEvent.setup();
    m11Api('student', { 'GET /api/m11/metrics-glossary': () => jsonResponse(200, glossary) });
    renderApp('/m11/phan-tich');
    await user.click(
      await screen.findByRole('button', { name: 'Giải thích: Điểm dự kiến của môn đang học' }),
    );
    expect(await screen.findByText(new RegExp(WARNING_NOTE))).toBeVisible();
  });

  it('ở trang chi tiết môn', async () => {
    const user = userEvent.setup();
    m11Api('student', { 'GET /api/m11/metrics-glossary': () => jsonResponse(200, glossary) });
    renderApp('/m11/phan-tich/mon/CNTT1188');
    await user.click(await screen.findByRole('button', { name: 'Giải thích: Cảnh báo từng môn' }));
    expect(await screen.findByText(new RegExp(WARNING_NOTE))).toBeVisible();
  });
});
