import { Pencil, Plus, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { MOTIFS } from '../../components/brand/motifs';
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
} from '../../components/ui';
import { STATUS_CHIPS } from '../../components/ui/StatusChip';

/** [chữ, nền] cần đạt 4,5:1; viền là [viền, nền] cần đạt 3:1. */
const COLOR_PAIRS = [
  ['--text-primary', '--surface-canvas'],
  ['--text-secondary', '--surface-canvas'],
  ['--text-primary', '--surface-card'],
  ['--text-secondary', '--surface-card'],
  ['--text-secondary', '--surface-sunken'],
  ['--text-link', '--surface-card'],
  ['--text-link', '--surface-canvas'],
  ['--text-on-primary', '--neu-primary'],
  ['--text-on-primary-muted', '--neu-primary'],
  ['--neu-primary', '--surface-card'],
  ['--success-text', '--success-bg'],
  ['--warning-text', '--warning-bg'],
  ['--danger-text', '--danger-bg'],
  ['--info-text', '--info-bg'],
  ['--text-on-primary', '--neu-red'],
  ['--border-strong', '--surface-card'],
  ['--neu-gray', '--surface-card'],
];
const TYPE_SCALE = ['12', '14', '16', '18', '20', '24', '30', '36'];
const RADII = ['sm', 'md', 'lg', 'xl'];
const SHADOWS = ['sm', 'md', 'lg'];
const VARIANTS = ['primary', 'secondary', 'ghost', 'danger'];
const SIZES = ['sm', 'md', 'lg'];
const SAMPLE_ROWS = [
  { id: 1, code: 'CNT101', name: 'Nhập môn lập trình (mẫu)', status: 'done' },
  { id: 2, code: null, name: 'Chuyên đề thực tế (mẫu)', status: 'in_progress' },
  { id: 3, code: 'MAU101', name: 'Giải tích (mẫu)', status: 'failed' },
];

/** Đọc màu thật của token từ trình duyệt, để bảng không lệch với tokens.css. */
function resolveColor(token) {
  const probe = document.createElement('span');
  probe.style.color = `var(${token})`;
  document.body.append(probe);
  const channels = window.getComputedStyle(probe).color.match(/\d+/g)?.slice(0, 3) ?? [0, 0, 0];
  probe.remove();
  return channels.map((channel) => parseInt(channel, 10));
}

function luminance(channels) {
  const [red, green, blue] = channels.map((channel) => {
    const ratio = channel / 255;
    return ratio <= 0.03928 ? ratio / 12.92 : ((ratio + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

function contrastText(foreground, background) {
  const [light, dark] = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  const ratio = Math.round(((light + 0.05) / (dark + 0.05)) * 100) / 100;
  return `${String(ratio).replace('.', ',')}:1`;
}

function ColorTable() {
  const [rows, setRows] = useState([]);
  useEffect(() => {
    setRows(
      COLOR_PAIRS.map(([foreground, background]) => ({
        foreground,
        background,
        ratio: contrastText(resolveColor(foreground), resolveColor(background)),
      })),
    );
  }, []);
  return (
    <div className="styleguide-swatches">
      {rows.map((row) => (
        <div
          key={`${row.foreground}${row.background}`}
          className="styleguide-swatch"
          style={{ background: `var(${row.background})`, color: `var(${row.foreground})` }}
        >
          <strong>{row.ratio}</strong>
          <span>{row.foreground}</span>
          <span>trên {row.background}</span>
        </div>
      ))}
    </div>
  );
}

function ToastDemo() {
  const { show } = useToast();
  return (
    <div className="form-actions">
      <Button variant="secondary" onClick={() => show('Đã lưu thông tin liên hệ.')}>
        Toast thành công
      </Button>
      <Button variant="secondary" onClick={() => show('Không lưu được.', 'error')}>
        Toast lỗi
      </Button>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <Card title={title} className="styleguide-section">
      {children}
    </Card>
  );
}

const noop = () => {};

export default function StyleguidePage() {
  const [panel, setPanel] = useState(false);
  return (
    <ToastProvider>
      <main id="main" className="styleguide">
        <PageHeader
          title="Hệ thống thiết kế NEU 2026"
          description="Chỉ có khi chạy dev, không nằm trong bản production."
          breadcrumb={[{ label: 'Dev' }, { label: 'Styleguide' }]}
          actions={<Button iconLeft={Plus}>Vùng hành động</Button>}
        />
        <Section title="Màu và tỷ lệ tương phản">
          <ColorTable />
        </Section>
        <Section title="Thang chữ Inter">
          {TYPE_SCALE.map((size) => (
            <p key={size} style={{ fontSize: `var(--font-${size})`, margin: 0 }}>
              {size}px · Học kỳ 3,11 Đại học Kinh tế Quốc dân
            </p>
          ))}
        </Section>
        <Section title="Bo góc và bóng">
          <div className="form-actions">
            {RADII.map((name) => (
              <span
                key={name}
                className="styleguide-box"
                style={{ borderRadius: `var(--radius-${name})` }}
              >
                {name}
              </span>
            ))}
            {SHADOWS.map((name) => (
              <span
                key={name}
                className="styleguide-box"
                style={{ boxShadow: `var(--shadow-${name})` }}
              >
                bóng {name}
              </span>
            ))}
          </div>
        </Section>
        <Section title="Họa tiết (19)">
          <div className="styleguide-motifs">
            {Object.entries(MOTIFS).map(([name, Motif]) => (
              <figure key={name}>
                <Motif bg="tint" fg="primary" />
                <figcaption>{name}</figcaption>
              </figure>
            ))}
          </div>
        </Section>
        <Section title="Button">
          {VARIANTS.map((variant) => (
            <div key={variant} className="form-actions styleguide-row">
              {SIZES.map((size) => (
                <Button key={size} variant={variant} size={size} iconLeft={Pencil}>
                  {variant} {size}
                </Button>
              ))}
              <Button variant={variant} loading>
                Đang tải
              </Button>
              <Button variant={variant} disabled iconRight={Trash2}>
                Bị khóa
              </Button>
            </div>
          ))}
        </Section>
        <Section title="Badge và StatusChip">
          <div className="form-actions styleguide-row">
            {['neutral', 'info', 'success', 'warning', 'danger', 'outline'].map((tone) => (
              <Badge key={tone} tone={tone}>
                {tone}
              </Badge>
            ))}
          </div>
          <div className="form-actions">
            {Object.keys(STATUS_CHIPS).map((status) => (
              <StatusChip key={status} status={status} />
            ))}
          </div>
        </Section>
        <Section title="MetricCard">
          <div className="grid-12">
            <div className="span-3">
              <MetricCard
                label="GPA tích lũy"
                value="3,11"
                hint="Phụ chú"
                info={<InfoPopover label="Giải thích">Công thức của chỉ số.</InfoPopover>}
              />
            </div>
            <div className="span-3">
              <MetricCard label="Biến thể nhấn mạnh" value="19" hint="Phụ chú" emphasis />
            </div>
            <div className="span-3">
              <MetricCard label="Chưa có dữ liệu" value="—" />
            </div>
            <div className="span-3 metric-card metric-card--skeleton">
              <Skeleton width="60%" />
              <Skeleton width="40%" height={36} />
              <Skeleton />
            </div>
          </div>
        </Section>
        <Section title="DataTable (dưới 768px thành thẻ, bấm tiêu đề để sắp xếp)">
          <DataTable
            ariaLabel="Bảng mẫu"
            rowKey={(row) => row.id}
            rows={SAMPLE_ROWS}
            columns={[
              {
                key: 'code',
                header: 'Mã môn',
                sortable: true,
                render: (row) => row.code ?? 'Chưa có mã',
              },
              { key: 'name', header: 'Tên môn', sortable: true },
              {
                key: 'status',
                header: 'Trạng thái',
                render: (row) => <StatusChip status={row.status} />,
              },
            ]}
          />
          <Pagination
            label="Phân trang mẫu"
            page={1}
            lastPage={3}
            summary="Trang 1 / 3"
            onPage={noop}
          />
        </Section>
        <Section title="Tabs">
          <Tabs
            label="Tabs mẫu"
            tabs={[
              { id: 'a', label: 'Tab một', content: <p>Nội dung tab một.</p> },
              { id: 'b', label: 'Tab hai', content: <p>Nội dung tab hai.</p> },
            ]}
          />
        </Section>
        <Section title="Input, Select, FormField, SearchBox">
          <div className="filter-bar">
            <FormField id="sg-a" label="Ô thường" hint="Gợi ý dưới ô">
              <Input defaultValue="Giá trị" />
            </FormField>
            <FormField id="sg-b" label="Ô có lỗi" errors={['Email không hợp lệ.']}>
              <Input defaultValue="sai" />
            </FormField>
            <FormField id="sg-c" label="Ô bị khóa">
              <Input disabled defaultValue="Không sửa được" />
            </FormField>
            <FormField id="sg-d" label="Select">
              <Select>
                <option>Lựa chọn một</option>
                <option>Lựa chọn hai</option>
              </Select>
            </FormField>
            <FormField id="sg-e" label="SearchBox">
              <SearchBox placeholder="Tìm kiếm" />
            </FormField>
          </div>
        </Section>
        <Section title="DropdownMenu, SidePanel, InfoPopover, Toast, Avatar">
          <div className="form-actions styleguide-row">
            <DropdownMenu
              trigger={<span>Mở menu</span>}
              items={[
                { label: 'Mục một', icon: Pencil, onSelect: noop },
                { label: 'Mục bị khóa', icon: Trash2, disabled: true },
              ]}
            />
            <Button variant="secondary" onClick={() => setPanel(true)}>
              Mở SidePanel
            </Button>
            <InfoPopover label="Thông tin thêm">Nội dung giải thích ngắn.</InfoPopover>
            <Avatar name="Sinh viên 01 (mẫu)" size="sm" />
            <Avatar name="Sinh viên 01 (mẫu)" size="md" />
            <Avatar name="Sinh viên 01 (mẫu)" size="lg" />
          </div>
          <ToastDemo />
          {panel && (
            <SidePanel title="SidePanel" onClose={() => setPanel(false)}>
              <p>Khóa focus, Esc để đóng, đóng thì trả focus.</p>
            </SidePanel>
          )}
        </Section>
        <Section title="Skeleton, EmptyState, ErrorState">
          <Skeleton height={44} />
          <div className="grid-12 styleguide-row">
            <div className="span-5">
              <EmptyState
                title="Chưa có dữ liệu"
                description="Mô tả ngắn."
                action={<Button>Hành động</Button>}
              />
            </div>
            <div className="span-7">
              <ErrorState title="Không tải được" description="Lỗi kết nối." onRetry={noop} />
            </div>
          </div>
        </Section>
      </main>
    </ToastProvider>
  );
}
