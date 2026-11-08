/**
 * Hai biểu đồ của trang Tổng quan (CR-08, D-306).
 * Tín chỉ là số nguyên từ /api/m11/credits nên tính phần trăm bằng số nguyên, không đổi kiểu.
 * GPA vẫn đổi sang số ở đúng một chỗ: toChartData của GpaTrendChart (Q78).
 */
import { useEffect, useRef, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { EmptyState } from '../../components/ui';
import { formatCount, formatDecimal, gradedPoints, NO_VALUE } from './format';
import { toChartData } from './GpaTrendChart';

const GPA_TICKS = [0, 1, 2, 3, 4];
const LABEL_SIZE = 12;
/** Nhãn ngoài biểu đồ tròn rộng nhất khoảng 56px ở cỡ 12px ("77 tín chỉ"), cộng khoảng cách tới viền. */
const PIE_LABEL_ROOM = 72;
const PIE_HEIGHT = 280;

export const PIE_PARTS = [
  { key: 'passed', label: 'Tín chỉ đã đạt', short: 'Đã đạt', color: 'var(--chart-passed)' },
  { key: 'failed', label: 'Tín chỉ chưa đạt', short: 'Chưa đạt', color: 'var(--chart-failed)' },
  {
    key: 'remaining',
    label: 'Tín chỉ chưa học',
    short: 'Chưa học',
    color: 'var(--chart-remaining)',
  },
];

/**
 * Phần trăm 1 chữ số thập phân, đơn vị là 0,1%, tổng luôn đúng 1000 (100,0%).
 * Làm tròn xuống rồi chia phần còn thiếu cho các phần có phần dư lớn nhất; bằng nhau thì phần đứng trước.
 */
export function roundTenths(amounts, total) {
  if (total <= 0) {
    return amounts.map(() => 0);
  }
  const floors = amounts.map((amount) => Math.floor((amount * 1000) / total));
  const order = amounts
    .map((amount, index) => ({ index, rest: (amount * 1000) % total }))
    .sort((a, b) => b.rest - a.rest || a.index - b.index);
  let missing = 1000 - floors.reduce((sum, item) => sum + item, 0);
  for (const { index } of order) {
    if (missing === 0) {
      break;
    }
    floors[index] += 1;
    missing -= 1;
  }
  return floors;
}

export function formatTenths(tenths) {
  return `${Math.floor(tenths / 10)},${tenths % 10}%`;
}

/**
 * Tổng = tín chỉ bắt buộc + mức tối thiểu của các nhóm tự chọn (tổng tín chỉ CTĐT).
 * Đã đạt = tổng trừ phần còn thiếu, nên môn ngoài CTĐT và phần vượt nhóm không tính.
 * Chưa đạt = tín chỉ nợ, không quá phần còn thiếu. Chưa học = phần còn lại, gồm cả đang học.
 * Không có quy chế (số đạt null) hoặc CTĐT không có tín chỉ thì không vẽ.
 */
export function creditPieData(credits) {
  const { required, elective_groups: groups, debt } = credits;
  if (required.passed_credits === null || debt === null) {
    return null;
  }
  const total = groups.reduce((sum, group) => sum + group.min_credits, required.total_credits);
  if (total <= 0) {
    return null;
  }
  const missing = groups.reduce(
    (sum, group) => sum + group.missing_credits,
    required.missing_credits,
  );
  const failed = Math.min(debt, missing);
  const amounts = [total - missing, failed, missing - failed];
  const tenths = roundTenths(amounts, total);
  return {
    total,
    parts: PIE_PARTS.map((part, index) => ({
      ...part,
      credits: amounts[index],
      tenths: tenths[index],
      percent: formatTenths(tenths[index]),
    })),
  };
}

/** Chỉ các kỳ đã có GPA, tính đến kỳ đang chọn; tên kỳ đầy đủ như dữ liệu. */
export function gpaBarData(points) {
  return toChartData(gradedPoints(points));
}

/** Bán kính theo bề rộng thật, chừa chỗ cho nhãn hai bên để nhãn không bị cắt ở cột hẹp. */
export function pieRadius(width) {
  return Math.max(40, Math.min(100, Math.floor(width / 2) - PIE_LABEL_ROOM));
}

function useWidth() {
  const ref = useRef(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const node = ref.current;
    if (!node || typeof window.ResizeObserver === 'undefined') {
      return undefined;
    }
    const observer = new window.ResizeObserver(([entry]) =>
      setWidth(Math.floor(entry.contentRect.width)),
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  return [ref, width];
}

function PieLabel({ cx, cy, midAngle, outerRadius, payload }) {
  if (payload.credits === 0) {
    return null;
  }
  const radian = Math.PI / 180;
  const radius = outerRadius + 12;
  const down = Math.sin(-midAngle * radian);
  const x = cx + radius * Math.cos(-midAngle * radian);
  const y = cy + radius * down;
  const anchor = x >= cx ? 'start' : 'end';
  // Khối 3 dòng: nhãn ở hai bên căn giữa theo điểm neo; ở đáy thì nằm dưới, ở đỉnh thì nằm trên hình.
  const firstLine = `${Math.round((-0.9 + 1.6 * down) * 100) / 100}em`;
  return (
    <text
      x={x}
      y={y}
      textAnchor={anchor}
      fill="var(--text-primary)"
      fontSize={LABEL_SIZE}
      className="credit-pie__label"
    >
      <tspan x={x} dy={firstLine}>
        {payload.short}
      </tspan>
      <tspan x={x} dy="1.25em" fontWeight={700}>
        {payload.percent}
      </tspan>
      <tspan x={x} dy="1.25em">
        {payload.credits} tín chỉ
      </tspan>
    </text>
  );
}

function pieSummary(data) {
  const [passed, failed, remaining] = data.parts;
  return (
    `Tổng ${data.total} tín chỉ theo CTĐT: đã đạt ${passed.credits} (${passed.percent}), ` +
    `chưa đạt ${failed.credits} (${failed.percent}), chưa học ${remaining.credits} ` +
    `(${remaining.percent}).`
  );
}

export function CreditPie({ credits }) {
  const [plotRef, width] = useWidth();
  const data = creditPieData(credits);
  if (!data) {
    return (
      <EmptyState
        compact
        title="Chưa vẽ được biểu đồ tín chỉ"
        description="Khóa này chưa có quy chế hoặc CTĐT chưa có tín chỉ."
      />
    );
  }
  return (
    <figure className="credit-pie">
      <figcaption className="visually-hidden">{pieSummary(data)}</figcaption>
      <div className="credit-pie__plot" aria-hidden="true" ref={plotRef}>
        {width > 0 && (
          <PieChart accessibilityLayer={false} width={width} height={PIE_HEIGHT}>
            <Pie
              data={data.parts}
              dataKey="credits"
              nameKey="label"
              cx="50%"
              cy="50%"
              startAngle={90}
              endAngle={-270}
              outerRadius={pieRadius(width)}
              stroke="var(--surface-card)"
              strokeWidth={2}
              isAnimationActive={false}
              labelLine={false}
              label={PieLabel}
              rootTabIndex={-1}
            >
              {data.parts.map((part) => (
                <Cell key={part.key} fill={part.color} />
              ))}
            </Pie>
          </PieChart>
        )}
      </div>
      <table className="visually-hidden">
        <caption>Tín chỉ theo CTĐT</caption>
        <thead>
          <tr>
            <th scope="col">Phần</th>
            <th scope="col">Tín chỉ</th>
            <th scope="col">Tỷ lệ</th>
          </tr>
        </thead>
        <tbody>
          {data.parts.map((part) => (
            <tr key={part.key}>
              <td>{part.label}</td>
              <td>{formatCount(part.credits)}</td>
              <td>{part.percent}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}

function BarTooltip({ active, payload }) {
  if (!active || !payload?.length) {
    return null;
  }
  const point = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <p>{point.name}</p>
      <p>
        <strong>Điểm trung bình {formatDecimal(point.raw)}</strong>
      </p>
    </div>
  );
}

function barSummary(bars) {
  if (bars.length === 0) {
    return 'Chưa có kỳ nào có điểm.';
  }
  const list = bars.map((bar) => `${bar.name}: ${formatDecimal(bar.raw)}`).join('; ');
  return `Điểm trung bình hệ 4 các kỳ đã có điểm: ${list}.`;
}

export function GpaBars({ trend }) {
  const bars = gpaBarData(trend.points);
  if (bars.length === 0) {
    return (
      <EmptyState
        compact
        title="Chưa có kỳ nào có điểm"
        description="Cột của mỗi kỳ hiện khi kỳ đó có kết quả."
      />
    );
  }
  return (
    <figure className="gpa-bars">
      <figcaption className="visually-hidden">{barSummary(bars)}</figcaption>
      <p className="chart-legend" aria-hidden="true">
        <span className="chart-legend__dot" />
        Điểm trung bình
      </p>
      <div className="gpa-bars__plot" aria-hidden="true">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            accessibilityLayer={false}
            data={bars}
            margin={{ top: 8, right: 8, bottom: 8, left: -24 }}
          >
            <CartesianGrid vertical={false} stroke="var(--border-subtle)" />
            <XAxis
              dataKey="name"
              interval={0}
              angle={-40}
              textAnchor="end"
              height={92}
              tick={{ fill: 'var(--text-secondary)', fontSize: LABEL_SIZE }}
              tickLine={false}
              axisLine={{ stroke: 'var(--border-subtle)' }}
            />
            <YAxis
              domain={[0, 4]}
              ticks={GPA_TICKS}
              allowDataOverflow
              tick={{ fill: 'var(--text-secondary)', fontSize: LABEL_SIZE }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip content={<BarTooltip />} cursor={{ fill: 'var(--surface-sunken)' }} />
            <Bar
              dataKey="plotted"
              fill="var(--neu-primary)"
              radius={[6, 6, 0, 0]}
              maxBarSize={72}
              isAnimationActive={false}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <table className="visually-hidden">
        <caption>Điểm trung bình theo kỳ</caption>
        <thead>
          <tr>
            <th scope="col">Học kỳ</th>
            <th scope="col">Điểm trung bình</th>
          </tr>
        </thead>
        <tbody>
          {bars.map((bar) => (
            <tr key={bar.name}>
              <td>{bar.name}</td>
              <td>{bar.raw === null ? NO_VALUE : formatDecimal(bar.raw)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
