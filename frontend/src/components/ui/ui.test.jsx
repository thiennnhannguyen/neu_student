import { act, fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Pencil } from 'lucide-react';
import { useState } from 'react';
import { MemoryRouter } from 'react-router';
import { describe, expect, it, vi } from 'vitest';
import {
  Avatar,
  Badge,
  Button,
  Card,
  DataTable,
  DropdownMenu,
  EmptyState,
  ErrorState,
  FormField,
  InfoPopover,
  Input,
  MetricCard,
  PageHeader,
  Pagination,
  SearchBox,
  Select,
  SidePanel,
  Skeleton,
  StatusChip,
  Tabs,
  ToastProvider,
  useToast,
} from '.';
import { initialsOf } from './Avatar';
import { STATUS_CHIPS } from './StatusChip';

function inRouter(node) {
  return render(<MemoryRouter>{node}</MemoryRouter>);
}

describe('Button', () => {
  it('mặc định là type button, có icon trang trí aria-hidden', () => {
    render(<Button iconLeft={Pencil}>Sửa</Button>);

    const button = screen.getByRole('button', { name: 'Sửa' });
    expect(button).toHaveAttribute('type', 'button');
    expect(button.querySelector('svg')).toHaveAttribute('aria-hidden', 'true');
    expect(button).toHaveClass('btn--primary', 'btn--md');
  });

  it('loading thì khóa và không gọi onClick', async () => {
    const onClick = vi.fn();
    render(
      <Button loading onClick={onClick}>
        Lưu
      </Button>,
    );

    const button = screen.getByRole('button', { name: 'Lưu' });
    expect(button).toBeDisabled();
    expect(button.querySelector('.spinner')).not.toBeNull();
    await userEvent.setup().click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('có to thì là liên kết', () => {
    inRouter(
      <Button to="/x" variant="ghost" size="lg">
        Đi
      </Button>,
    );

    expect(screen.getByRole('link', { name: 'Đi' })).toHaveAttribute('href', '/x');
  });
});

describe('Card, PageHeader, Badge, Avatar, Skeleton', () => {
  it('Card có header, body, footer', () => {
    render(
      <Card title="Tiêu đề" actions={<button type="button">A</button>} footer="Chân">
        Thân
      </Card>,
    );

    expect(screen.getByRole('heading', { name: 'Tiêu đề' })).toBeInTheDocument();
    expect(screen.getByText('Chân')).toHaveClass('ui-card__footer');
  });

  it('PageHeader có h1, breadcrumb, hành động; họa tiết aria-hidden, không nhận focus', () => {
    const { container } = inRouter(
      <PageHeader
        title="Trang"
        description="Mô tả"
        breadcrumb={[{ label: 'Gốc', to: '/' }, { label: 'Trang' }]}
        actions={<button type="button">Làm</button>}
      />,
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Trang' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Gốc' })).toHaveAttribute('href', '/');
    const motif = container.querySelector('.page-header__motif');
    expect(motif).toHaveAttribute('aria-hidden', 'true');
    expect(motif.querySelector('a, button')).toBeNull();
  });

  it.each([
    ['Sinh viên 01 (mẫu)', 'SV'],
    ['Quản trị viên (mẫu)', 'QV'],
    ['admin', 'A'],
    ['(mẫu)', '?'],
  ])('Avatar: %s -> %s', (name, expected) => {
    expect(initialsOf(name)).toBe(expected);
  });

  it('Avatar và Skeleton chỉ trang trí', () => {
    const { container } = render(
      <>
        <Avatar name="A B" />
        <Skeleton />
        <Badge tone="danger">X</Badge>
      </>,
    );

    expect(container.querySelector('.avatar')).toHaveAttribute('aria-hidden', 'true');
    expect(container.querySelector('.skeleton')).toHaveAttribute('aria-hidden', 'true');
    expect(screen.getByText('X')).toHaveClass('badge--danger');
  });
});

describe('StatusChip', () => {
  it('có đủ 6 trạng thái môn và các mức cảnh báo', () => {
    expect(Object.keys(STATUS_CHIPS)).toEqual(
      expect.arrayContaining([
        'done',
        'done_via_equivalency',
        'exempt',
        'in_progress',
        'failed',
        'not_started',
        'normal',
        'watch',
        'warning',
        'insufficient_data',
      ]),
    );
  });

  it.each(Object.entries(STATUS_CHIPS))('%s luôn có biểu tượng và chữ', (status, chip) => {
    render(<StatusChip status={status} />);

    const element = screen.getByText(chip.label);
    expect(element.querySelector('svg')).toHaveAttribute('aria-hidden', 'true');
  });

  it('chỉ trạng thái đã đạt mới có màu thành công (R6)', () => {
    const courseStates = ['in_progress', 'failed', 'not_started'];

    for (const status of courseStates) {
      expect(STATUS_CHIPS[status].tone).not.toBe('success');
    }
  });

  it('trạng thái lạ vẫn hiện chữ', () => {
    render(<StatusChip status="la" />);

    expect(screen.getByText('la')).toBeInTheDocument();
  });
});

describe('MetricCard', () => {
  it('có nhãn, giá trị, phụ chú; có to thì cả thẻ là liên kết, nút i vẫn bấm được', () => {
    inRouter(
      <MetricCard
        label="GPA"
        value="3,11"
        hint="Phụ"
        to="/x"
        info={<button type="button">i</button>}
      />,
    );

    expect(screen.getByRole('link', { name: 'GPA' })).toHaveAttribute('href', '/x');
    expect(screen.getByText('3,11')).toHaveClass('metric-card__value');
    expect(screen.getByRole('button', { name: 'i' })).toBeInTheDocument();
  });

  it('biến thể nhấn mạnh, không có liên kết', () => {
    const { container } = render(<MetricCard label="X" value="1" emphasis />);

    expect(container.firstChild).toHaveClass('metric-card--emphasis');
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});

describe('DataTable', () => {
  const ROWS = [
    { id: 1, code: 'B', name: 'Hai' },
    { id: 2, code: null, name: 'Ba' },
    { id: 3, code: 'A', name: 'Một' },
  ];
  const COLUMNS = [
    { key: 'code', header: 'Mã', sortable: true, render: (row) => row.code ?? 'Chưa có mã' },
    { key: 'name', header: 'Tên' },
  ];

  function firstCells() {
    return screen
      .getAllByRole('row')
      .slice(1)
      .map((row) => within(row).getAllByRole('cell')[0].textContent);
  }

  function renderTable() {
    return render(
      <DataTable
        columns={COLUMNS}
        rows={ROWS}
        rowKey={(row) => row.id}
        ariaLabel="Bảng"
        caption="Chú thích"
      />,
    );
  }

  it('giữ thứ tự gốc khi chưa sắp xếp; sắp xếp tăng rồi giảm, null luôn ở cuối khi tăng', async () => {
    const user = userEvent.setup();
    renderTable();
    const header = screen.getByRole('columnheader', { name: 'Mã' });

    expect(firstCells()).toEqual(['B', 'Chưa có mã', 'A']);
    expect(header).toHaveAttribute('aria-sort', 'none');

    await user.click(within(header).getByRole('button'));
    expect(firstCells()).toEqual(['A', 'B', 'Chưa có mã']);
    expect(header).toHaveAttribute('aria-sort', 'ascending');

    await user.click(within(header).getByRole('button'));
    expect(firstCells()).toEqual(['Chưa có mã', 'B', 'A']);
    expect(header).toHaveAttribute('aria-sort', 'descending');
  });

  it('sắp xếp bằng bàn phím', async () => {
    const user = userEvent.setup();
    renderTable();

    within(screen.getByRole('columnheader', { name: 'Mã' }))
      .getByRole('button')
      .focus();
    await user.keyboard('{Enter}');

    expect(firstCells()[0]).toBe('A');
  });

  it('cột không sắp xếp không có nút và aria-sort', () => {
    renderTable();

    const header = screen.getByRole('columnheader', { name: 'Tên' });
    expect(header).not.toHaveAttribute('aria-sort');
    expect(within(header).queryByRole('button')).toBeNull();
  });

  it('chế độ thẻ: mỗi ô có data-label theo tên cột; vùng cuộn nhận focus', () => {
    renderTable();

    const cells = within(screen.getAllByRole('row')[1]).getAllByRole('cell');
    expect(cells.map((cell) => cell.dataset.label)).toEqual(['Mã', 'Tên']);
    expect(screen.getByRole('region', { name: 'Bảng' })).toHaveAttribute('tabindex', '0');
  });

  it('CSS chuyển thành thẻ dưới 768px', async () => {
    const { readFileSync } = await import('node:fs');
    const css = readFileSync('src/styles/ui.css', 'utf8');

    expect(css).toMatch(
      /@media \(max-width: 767\.98px\)[\s\S]*\.ui-table td::before[\s\S]*attr\(data-label\)/,
    );
  });
});

describe('Tabs', () => {
  function renderTabs() {
    render(
      <Tabs
        label="Mẫu"
        tabs={[
          { id: 'a', label: 'Một', content: 'Nội dung một' },
          { id: 'b', label: 'Hai', content: 'Nội dung hai' },
          { id: 'c', label: 'Ba', content: 'Nội dung ba' },
        ]}
      />,
    );
  }

  it('bấm chuột đổi tab, chỉ tab đang chọn nhận Tab', async () => {
    const user = userEvent.setup();
    renderTabs();

    expect(screen.getByRole('tab', { name: 'Một' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: 'Hai' })).toHaveAttribute('tabindex', '-1');
    await user.click(screen.getByRole('tab', { name: 'Hai' }));

    expect(screen.getByRole('tabpanel')).toHaveTextContent('Nội dung hai');
    expect(screen.getByRole('tabpanel')).toHaveAccessibleName('Hai');
  });

  it('phím mũi tên, Home, End; quay vòng ở hai đầu', async () => {
    const user = userEvent.setup();
    renderTabs();
    screen.getByRole('tab', { name: 'Một' }).focus();

    await user.keyboard('{ArrowLeft}');
    expect(screen.getByRole('tab', { name: 'Ba' })).toHaveFocus();
    await user.keyboard('{ArrowRight}');
    expect(screen.getByRole('tab', { name: 'Một' })).toHaveFocus();
    await user.keyboard('{End}');
    expect(screen.getByRole('tabpanel')).toHaveTextContent('Nội dung ba');
    await user.keyboard('{Home}');
    expect(screen.getByRole('tabpanel')).toHaveTextContent('Nội dung một');
    await user.keyboard('a');
    expect(screen.getByRole('tabpanel')).toHaveTextContent('Nội dung một');
  });
});

describe('FormField, SearchBox, Select', () => {
  it('gắn label, gợi ý, lỗi vào ô', () => {
    render(
      <FormField id="x" label="Nhãn" hint="Gợi ý" errors={['Sai.', 'Thiếu.']}>
        <Input />
      </FormField>,
    );

    const input = screen.getByLabelText('Nhãn');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAccessibleDescription('Sai. Thiếu. Gợi ý');
  });

  it('không lỗi thì không có aria-invalid', () => {
    render(
      <FormField id="y" label="Nhãn">
        <Select>
          <option>A</option>
        </Select>
      </FormField>,
    );

    expect(screen.getByLabelText('Nhãn')).not.toHaveAttribute('aria-invalid');
    expect(screen.getByLabelText('Nhãn')).not.toHaveAttribute('aria-describedby');
  });

  it('SearchBox nhận id, aria từ FormField và là ô tìm kiếm', () => {
    render(
      <FormField id="z" label="Tìm" errors={['Sai.']}>
        <SearchBox />
      </FormField>,
    );

    expect(screen.getByRole('searchbox', { name: 'Tìm' })).toHaveAttribute('aria-invalid', 'true');
  });
});

describe('Pagination', () => {
  it('khóa nút ở hai đầu, gọi đúng trang', async () => {
    const onPage = vi.fn();
    const user = userEvent.setup();
    const { rerender } = render(
      <Pagination label="P" page={1} lastPage={2} summary="1/2" onPage={onPage} />,
    );

    expect(screen.getByRole('button', { name: 'Trang trước' })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: 'Trang sau' }));
    expect(onPage).toHaveBeenCalledWith(2);

    rerender(<Pagination label="P" page={2} lastPage={2} summary="2/2" onPage={onPage} />);
    expect(screen.getByRole('button', { name: 'Trang sau' })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: 'Trang trước' }));
    expect(onPage).toHaveBeenCalledWith(1);
  });
});

function PanelHost() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>
        Mở
      </button>
      {open && (
        <SidePanel title="Panel" onClose={() => setOpen(false)}>
          <input aria-label="Ô" />
          <button type="button">Cuối</button>
        </SidePanel>
      )}
    </>
  );
}

describe('SidePanel', () => {
  async function open(user) {
    screen.getByRole('button', { name: 'Mở' }).focus();
    await user.keyboard('{Enter}');
    return screen.getByRole('dialog', { name: 'Panel' });
  }

  it('focus vào nút đóng, khóa Tab ở cả hai chiều', async () => {
    const user = userEvent.setup();
    render(<PanelHost />);
    const dialog = await open(user);
    const close = within(dialog).getByRole('button', { name: 'Đóng' });
    const last = within(dialog).getByRole('button', { name: 'Cuối' });

    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(close).toHaveFocus();
    await user.tab({ shift: true });
    expect(last).toHaveFocus();
    await user.tab();
    expect(close).toHaveFocus();
    await user.tab();
    expect(within(dialog).getByRole('textbox', { name: 'Ô' })).toHaveFocus();
  });

  it('Esc đóng và trả focus; bấm nền đóng; bấm trong panel không đóng', async () => {
    const user = userEvent.setup();
    const { container } = render(<PanelHost />);
    await open(user);

    await user.keyboard('{Escape}');
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(screen.getByRole('button', { name: 'Mở' })).toHaveFocus();

    await open(user);
    fireEvent.mouseDown(screen.getByRole('dialog'));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    fireEvent.mouseDown(container.querySelector('.side-panel__backdrop'));
    expect(screen.queryByRole('dialog')).toBeNull();
  });
});

describe('InfoPopover', () => {
  it('mở, Esc đóng và trả focus, bấm ngoài đóng', async () => {
    const user = userEvent.setup();
    render(<InfoPopover label="Thêm">Nội dung</InfoPopover>);
    const button = screen.getByRole('button', { name: 'Thêm' });

    await user.click(button);
    expect(screen.getByText('Nội dung')).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-expanded', 'true');

    await user.keyboard('{Escape}');
    expect(screen.queryByText('Nội dung')).toBeNull();
    expect(button).toHaveFocus();

    await user.click(button);
    fireEvent.mouseDown(document.body);
    expect(screen.queryByText('Nội dung')).toBeNull();
  });
});

describe('DropdownMenu', () => {
  function renderMenu(onSelect = vi.fn()) {
    inRouter(
      <DropdownMenu
        trigger="Tài khoản"
        header={<p>Đầu menu</p>}
        items={[
          { label: 'Hồ sơ', to: '/ho-so' },
          { label: 'Bị khóa', disabled: true, onSelect },
          { label: 'Đăng xuất', onSelect },
        ]}
      />,
    );
    return onSelect;
  }

  it('mở bằng chuột, focus mục đầu, có aria-expanded', async () => {
    const user = userEvent.setup();
    renderMenu();
    const trigger = screen.getByRole('button', { name: 'Tài khoản' });

    expect(trigger).toHaveAttribute('aria-haspopup', 'menu');
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
    await user.click(trigger);

    expect(trigger).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('menuitem', { name: 'Hồ sơ' })).toHaveFocus();
    expect(screen.getByText('Đầu menu')).toBeInTheDocument();
  });

  it('mũi tên bỏ qua mục bị khóa, quay vòng; Home, End', async () => {
    const user = userEvent.setup();
    renderMenu();
    screen.getByRole('button', { name: 'Tài khoản' }).focus();
    await user.keyboard('{ArrowDown}');
    const first = screen.getByRole('menuitem', { name: 'Hồ sơ' });
    const last = screen.getByRole('menuitem', { name: 'Đăng xuất' });

    expect(first).toHaveFocus();
    await user.keyboard('{ArrowDown}');
    expect(last).toHaveFocus();
    await user.keyboard('{ArrowDown}');
    expect(first).toHaveFocus();
    await user.keyboard('{ArrowUp}');
    expect(last).toHaveFocus();
    await user.keyboard('{Home}');
    expect(first).toHaveFocus();
    await user.keyboard('{End}');
    expect(last).toHaveFocus();
  });

  it('Esc đóng và trả focus; Tab đóng; bấm ngoài đóng', async () => {
    const user = userEvent.setup();
    renderMenu();
    const trigger = screen.getByRole('button', { name: 'Tài khoản' });

    await user.click(trigger);
    await user.keyboard('{Escape}');
    expect(screen.queryByRole('menu')).toBeNull();
    expect(trigger).toHaveFocus();

    await user.click(trigger);
    await user.tab();
    expect(screen.queryByRole('menu')).toBeNull();

    await user.click(trigger);
    fireEvent.mouseDown(document.body);
    expect(screen.queryByRole('menu')).toBeNull();
  });

  it('chọn mục gọi onSelect và đóng; mục bị khóa không làm gì', async () => {
    const user = userEvent.setup();
    const onSelect = renderMenu();
    const trigger = screen.getByRole('button', { name: 'Tài khoản' });

    await user.click(trigger);
    await user.click(screen.getByRole('menuitem', { name: 'Bị khóa' }));
    expect(onSelect).not.toHaveBeenCalled();
    expect(screen.getByRole('menu')).toBeInTheDocument();

    await user.click(screen.getByRole('menuitem', { name: 'Đăng xuất' }));
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('menu')).toBeNull();
  });

  it('mục liên kết đóng menu khi bấm', async () => {
    const user = userEvent.setup();
    renderMenu();

    await user.click(screen.getByRole('button', { name: 'Tài khoản' }));
    await user.click(screen.getByRole('menuitem', { name: 'Hồ sơ' }));

    expect(screen.queryByRole('menu')).toBeNull();
  });
});

describe('EmptyState, ErrorState', () => {
  it('EmptyState có minh họa aria-hidden, mức tiêu đề tùy chọn', () => {
    const { container } = render(
      <EmptyState heading="h1" title="Rỗng" description="Mô tả" action="X" />,
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Rỗng' })).toBeInTheDocument();
    expect(container.querySelector('.motif-mosaic')).toHaveAttribute('aria-hidden', 'true');
    expect(container.querySelector('.motif-mosaic').style).toBeDefined();
  });

  it('ErrorState là alert, có Thử lại; không có onRetry thì không có nút', async () => {
    const onRetry = vi.fn();
    const { rerender } = render(
      <ErrorState title="Lỗi" description="Chi tiết" onRetry={onRetry} />,
    );

    expect(screen.getByRole('alert')).toHaveTextContent('Chi tiết');
    await userEvent.setup().click(screen.getByRole('button', { name: 'Thử lại' }));
    expect(onRetry).toHaveBeenCalledTimes(1);

    rerender(<ErrorState title="Lỗi" />);
    expect(screen.queryByRole('button')).toBeNull();
  });
});

function ToastHost() {
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

describe('Toast', () => {
  it('hiện trong vùng aria-live, đóng được bằng nút', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <ToastHost />
      </ToastProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Ok' }));
    expect(screen.getByText('Đã lưu')).toHaveAttribute('aria-live', 'polite');
    await user.click(screen.getByRole('button', { name: 'Lỗi' }));
    expect(screen.getByText('Hỏng').closest('.toast')).toHaveClass('toast--error');

    await user.click(screen.getAllByRole('button', { name: 'Đóng thông báo' })[0]);
    expect(screen.queryByText('Đã lưu')).toBeNull();
  });

  it('tự ẩn sau 5 giây; gỡ provider thì hủy hẹn giờ', () => {
    vi.useFakeTimers();
    try {
      const { unmount } = render(
        <ToastProvider>
          <ToastHost />
        </ToastProvider>,
      );
      fireEvent.click(screen.getByRole('button', { name: 'Ok' }));
      expect(screen.getByText('Đã lưu')).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(5000);
      });
      expect(screen.queryByText('Đã lưu')).toBeNull();

      fireEvent.click(screen.getByRole('button', { name: 'Ok' }));
      unmount();
      expect(vi.getTimerCount()).toBe(0);
    } finally {
      vi.useRealTimers();
    }
  });
});
