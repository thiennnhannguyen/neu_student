import {
  Area,
  CartesianGrid,
  ComposedChart,
  LabelList,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { formatDecimal } from './format';

const GPA_TICKS = [0, 1, 2, 3, 4];

export function shortSemesterName(name) {
  const match = name.match(/^(HK\d) \d{2}(\d{2})-\d{2}(\d{2})/);
  return match ? `${match[1]} ${match[2]}-${match[3]}` : name;
}

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) {
    return null;
  }
  const point = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <p>{point.name}</p>
      <p>
        <strong>GPA {formatDecimal(point.raw)}</strong>
      </p>
    </div>
  );
}

/** File duy nhất được đổi GPA sang số, và chỉ để vẽ. Tooltip và bảng vẫn dùng chuỗi gốc (Q78). */
export function toChartData(points) {
  return points.map((point) => ({
    label: shortSemesterName(point.name),
    name: point.name,
    raw: point.value,
    plotted: point.value === null ? null : Number(point.value),
  }));
}

/** Ngưỡng GPA của quy chế, lấy từ /api/m11/risks. Khóa không có quy chế thì không có đường ngưỡng. */
export function gpaThresholds(outcomes) {
  const evidence = outcomes.find((outcome) => outcome.rule_code === 'gpa')?.evidence;
  return evidence?.warning_below
    ? { warning: evidence.warning_below, watch: evidence.watch_below }
    : null;
}

function thresholdLabel(text, value, color) {
  return {
    value: `${text} ${formatDecimal(value)}`,
    position: 'insideBottomRight',
    fill: color,
    fontSize: 12,
  };
}

export default function GpaTrendChart({ trend, thresholds = null }) {
  const data = toChartData(trend.points);
  return (
    <figure className="trend-chart">
      <figcaption>{trend.summary}</figcaption>
      <div className="trend-chart__plot" aria-hidden="true">
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data} margin={{ top: 24, right: 16, bottom: 0, left: -24 }}>
            <CartesianGrid vertical={false} stroke="var(--border-subtle)" />
            <XAxis
              dataKey="label"
              tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: 'var(--border-subtle)' }}
              interval="preserveStartEnd"
              padding={{ left: 24, right: 24 }}
            />
            <YAxis
              domain={[0, 4]}
              ticks={GPA_TICKS}
              tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip content={<ChartTooltip />} cursor={{ stroke: 'var(--neu-mid)' }} />
            {/* y là chuỗi từ API: thang đo tự đọc, không cần đổi sang số trong mã (Q78). */}
            {thresholds?.watch && (
              <ReferenceLine
                y={thresholds.watch}
                stroke="var(--warning-text)"
                strokeDasharray="4 4"
                strokeOpacity={0.6}
                label={thresholdLabel('Ngưỡng chú ý', thresholds.watch, 'var(--warning-text)')}
              />
            )}
            {thresholds && (
              <ReferenceLine
                y={thresholds.warning}
                stroke="var(--danger-text)"
                strokeDasharray="6 4"
                label={thresholdLabel('Ngưỡng cảnh báo', thresholds.warning, 'var(--danger-text)')}
              />
            )}
            <Area
              type="linear"
              dataKey="plotted"
              stroke="none"
              fill="var(--neu-primary)"
              fillOpacity={0.1}
              activeDot={false}
              isAnimationActive={false}
              connectNulls={false}
            />
            <Line
              type="linear"
              dataKey="plotted"
              stroke="var(--neu-primary)"
              strokeWidth={2}
              dot={{
                r: 4,
                fill: 'var(--neu-primary)',
                stroke: 'var(--surface-card)',
                strokeWidth: 2,
              }}
              activeDot={{ r: 6 }}
              isAnimationActive={false}
              connectNulls={false}
            >
              <LabelList
                dataKey="raw"
                position="top"
                formatter={formatDecimal}
                fill="var(--text-primary)"
                fontSize={12}
                stroke="var(--surface-card)"
                strokeWidth={3}
                paintOrder="stroke"
              />
            </Line>
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      {thresholds && (
        <p className="visually-hidden">
          Ngưỡng cảnh báo {formatDecimal(thresholds.warning)}
          {thresholds.watch ? `; ngưỡng chú ý ${formatDecimal(thresholds.watch)}` : ''}.
        </p>
      )}
      <table className="visually-hidden">
        <caption>GPA từng học kỳ</caption>
        <thead>
          <tr>
            <th scope="col">Học kỳ</th>
            <th scope="col">GPA</th>
          </tr>
        </thead>
        <tbody>
          {trend.points.map((point) => (
            <tr key={point.semester_id}>
              <td>{point.name}</td>
              <td>{formatDecimal(point.value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
