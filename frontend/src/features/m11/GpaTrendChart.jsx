import {
  CartesianGrid,
  Line,
  LineChart,
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

export default function GpaTrendChart({ trend }) {
  const data = toChartData(trend.points);
  return (
    <figure className="trend-chart">
      <figcaption>{trend.summary}</figcaption>
      <div className="trend-chart__plot" aria-hidden="true">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 16, right: 16, bottom: 0, left: -24 }}>
            <CartesianGrid vertical={false} stroke="var(--border-subtle)" />
            <XAxis
              dataKey="label"
              tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: 'var(--border-subtle)' }}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[0, 4]}
              ticks={GPA_TICKS}
              tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip content={<ChartTooltip />} cursor={{ stroke: 'var(--neu-mid)' }} />
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
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
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
