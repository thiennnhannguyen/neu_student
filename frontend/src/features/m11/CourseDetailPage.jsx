/**
 * Trang chi tiết môn đang học (CR-13, D-314): /m11/phan-tich/mon/:courseId, giữ ?student= cho cố
 * vấn và quản trị. Mọi số do backend tính; giao diện chỉ hiển thị chuỗi (Q78). Biểu đồ nhỏ dùng
 * trường số nguyên `plot` của API, chỉ để vẽ.
 */
import { ArrowLeft } from 'lucide-react';
import { useState } from 'react';
import { Link, useLocation, useParams } from 'react-router';
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { usePageLabel } from '../../components/PageLabelContext';
import { Button, Card, DataTable, PageHeader, StatusChip } from '../../components/ui';
import WeeklyReportHistory, { weeklySummaryText } from '../weeklyReport/WeeklyReportHistory';
import {
  courseCode,
  formatCount,
  formatDay,
  formatDecimal,
  formatSignedDecimal,
  weekdayName,
  withQuery,
} from './format';
import M11Page from './M11Page';
import MetricInfo from './MetricInfo';
import { CONFIDENCE, DISCLAIMER, LevelMark, rangeText } from './prediction';
import { ASSIGNMENT_SCORE, PROCESS_SCORE, ScoreHelp, TEST_SCORE } from './scoreHelp';
import { carrySearch } from './scopeQuery';
import useApiResource from './useApiResource';
import { ResourceView } from './ui';

/** "0.10" → "10%", "1.00" → "100%": tách chuỗi, không đổi sang số (Q78). */
export function percentText(weight) {
  const [whole, fraction = '00'] = weight.split('.');
  const digits = `${whole === '0' ? '' : whole}${fraction.padEnd(2, '0')}`.replace(/^0(?=\d)/, '');
  return `${digits}%`;
}

const BASELINE_SOURCE = {
  group: (baseline) => `trung bình nhóm ${baseline.group_name} (${baseline.courses} môn đã học)`,
  all: (baseline) => `trung bình các môn đã học (${baseline.courses} môn)`,
  default: () => 'mức nền mặc định',
};

const TARGET_LABEL = { C: 'Đạt C (5,5)', B: 'Đạt B (7,0)', A: 'Đạt A (8,5)' };

function baselineText(baseline) {
  const describe = BASELINE_SOURCE[baseline.source] ?? BASELINE_SOURCE.all;
  return `${formatDecimal(baseline.value)} – ${describe(baseline)}`;
}

function Summary({ prediction, studentId }) {
  if (prediction.level === 'insufficient') {
    return (
      <Card className="prediction-summary">
        <h2 className="section-heading">Điểm dự kiến</h2>
        <p className="prediction-summary__score">Chưa đủ dữ liệu</p>
        <p>Chưa có dữ liệu LMS hoặc môn chưa có buổi học nào.</p>
      </Card>
    );
  }
  const reasons = prediction.reasons.slice(0, 2);
  return (
    <Card className="prediction-summary">
      <h2 className="section-heading">
        Điểm dự kiến
        <MetricInfo metricKey="course_warning" label="Cảnh báo từng môn" studentId={studentId} />
      </h2>
      {prediction.level === 'barred' ? (
        <p className="prediction-summary__score">
          <LevelMark level="barred" />
        </p>
      ) : (
        <>
          <p className="prediction-summary__score">
            <span className="prediction-summary__value">{formatDecimal(prediction.score)}</span>
            <span className="prediction-summary__letter">{prediction.letter}</span>
          </p>
          <dl className="detail-list">
            <div>
              <dt>Khoảng dự kiến</dt>
              <dd>{rangeText(prediction.range)}</dd>
            </div>
            <div>
              <dt>Độ tin cậy</dt>
              <dd>
                {CONFIDENCE[prediction.confidence]}
                <MetricInfo
                  metricKey="prediction_range"
                  label="Khoảng dự kiến và độ tin cậy"
                  studentId={studentId}
                />
              </dd>
            </div>
            <div>
              <dt>Mức cảnh báo</dt>
              <dd>
                <LevelMark level={prediction.level} />
              </dd>
            </div>
          </dl>
        </>
      )}
      {reasons.length > 0 ? (
        <ul className="prediction-reasons" aria-label="Lý do">
          {reasons.map((reason) => (
            <li key={reason.code}>
              <LevelMark level={reason.level} />
              <span>{reason.text}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p>Không có dấu hiệu cần chú ý.</p>
      )}
    </Card>
  );
}

function componentRows(prediction) {
  const [attendance, process, final] = prediction.components;
  const { held, present } = prediction.attendance;
  return [
    {
      key: 'attendance',
      name: 'Chuyên cần',
      weight: attendance.weight,
      value: attendance.value,
      basis: `Ước lượng từ số thật: có mặt ${formatCount(present)}/${formatCount(held)} buổi đã học, giả định giữ tỷ lệ tới cuối kỳ (vắng có phép tính như vắng).`,
    },
    {
      key: 'process',
      name: 'Quá trình',
      weight: process.weight,
      value: process.value,
      basis:
        process.current === null
          ? `Ước lượng: chưa có bài nào được tính, dùng mức nền ${formatDecimal(prediction.baseline.value)}.`
          : `Số thật và ước lượng: điểm quá trình hiện tại ${formatDecimal(process.current)} trên ${formatCount(process.items)} bài tập, bài kiểm tra; kéo về mức nền ${formatDecimal(prediction.baseline.value)} vì còn ít bài.`,
    },
    {
      key: 'final',
      name: 'Cuối kỳ',
      weight: final.weight,
      value: final.value,
      basis: `Ước lượng: mức nền ${baselineText(prediction.baseline)}, điều chỉnh ${formatSignedDecimal(prediction.adjust_total)}.`,
    },
  ];
}

const COMPONENT_COLUMNS = [
  { key: 'name', header: 'Thành phần', rowHeader: true, render: (row) => row.name },
  { key: 'weight', header: 'Trọng số', render: (row) => percentText(row.weight) },
  { key: 'value', header: 'Điểm dùng để tính', render: (row) => formatDecimal(row.value) },
  { key: 'basis', header: 'Số thật hay ước lượng', render: (row) => row.basis },
];

function Components({ prediction }) {
  return (
    <section aria-labelledby="components-title" className="stack">
      <h2 id="components-title" className="section-heading">
        Thành phần điểm
      </h2>
      <DataTable
        caption="Thành phần điểm dự kiến"
        columns={COMPONENT_COLUMNS}
        rows={componentRows(prediction)}
        rowKey={(row) => row.key}
      />
      {prediction.adjustments.length > 0 && (
        <div>
          <h3 className="subsection-heading">Điều chỉnh điểm cuối kỳ (tổng giới hạn ±1,5)</h3>
          <ul className="adjustment-list">
            {prediction.adjustments.map((item) => (
              <li key={item.code}>
                <span>{item.text}</span>
                <span className="adjustment-list__value">{formatSignedDecimal(item.value)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function targetText(target) {
  if (target.status === 'unreachable') {
    return 'Không đạt được';
  }
  if (target.status === 'secured') {
    return 'Đã chắc chắn';
  }
  return formatDecimal(target.needed);
}

function Targets({ targets }) {
  if (targets.length === 0) {
    return null;
  }
  return (
    <section aria-labelledby="targets-title">
      <h2 id="targets-title" className="section-heading">
        Cuối kỳ cần bao nhiêu điểm
      </h2>
      <dl className="detail-list target-list">
        {targets.map((target) => (
          <div key={target.letter}>
            <dt>{TARGET_LABEL[target.letter] ?? target.letter}</dt>
            <dd>{targetText(target)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

const SCORE_TICKS = [0, 2, 4, 6, 8, 10];
// Ngưỡng vẽ trên biểu đồ: điểm đạt 4,5 và mức C 5,5 (giá trị mẫu của D-314).
const CHART_LINES = [
  { y: 4.5, text: 'Ngưỡng đạt 4,5', color: 'var(--danger-text)' },
  { y: 5.5, text: 'Mức C 5,5', color: 'var(--warning-text)' },
];

function WeeklyTooltip({ active, payload }) {
  if (!active || !payload?.length) {
    return null;
  }
  const point = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <p>
        <strong>
          {point.name}: {formatDecimal(point.raw)}
        </strong>
      </p>
    </div>
  );
}

/** `plot` là số nguyên do backend tính (điểm × 100), chỉ để vẽ; nhãn và bảng dùng chuỗi (Q78). */
export function toWeeklyData(weekly) {
  return weekly
    .filter((point) => point.plot !== null)
    .map((point) => ({
      label: `T${point.week_no}`,
      name: `Tuần ${point.week_no}`,
      raw: point.score,
      plotted: point.plot / 100,
    }));
}

/**
 * Điểm dự kiến tính lại trên từng bản chụp LMS (CR-13b): rộng hết khối, trục 0–10, ngưỡng 4,5 và
 * 5,5, nhãn từng tuần. Có bảng ẩn cho trình đọc màn hình.
 */
export function WeeklyChart({ weekly }) {
  const data = toWeeklyData(weekly);
  if (data.length < 2) {
    return null;
  }
  const text = data.map((point) => `${point.name.toLowerCase()}: ${formatDecimal(point.raw)}`);
  return (
    <figure className="weekly-chart">
      <figcaption className="section-heading">Điểm dự kiến theo tuần</figcaption>
      <div
        className="weekly-chart__plot"
        role="img"
        aria-label={`Điểm dự kiến theo tuần: ${text.join('; ')}`}
      >
        <ResponsiveContainer width="100%" height={260}>
          <LineChart
            accessibilityLayer={false}
            data={data}
            margin={{ top: 16, right: 16, bottom: 0, left: -20 }}
          >
            <CartesianGrid vertical={false} stroke="var(--border-subtle)" />
            <XAxis
              dataKey="label"
              interval={0}
              tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: 'var(--border-subtle)' }}
              padding={{ left: 16, right: 16 }}
            />
            <YAxis
              domain={[0, 10]}
              ticks={SCORE_TICKS}
              tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip content={<WeeklyTooltip />} cursor={{ stroke: 'var(--neu-mid)' }} />
            {CHART_LINES.map((line) => (
              <ReferenceLine
                key={line.text}
                y={line.y}
                stroke={line.color}
                strokeDasharray="6 4"
                label={{
                  value: line.text,
                  position: 'insideBottomRight',
                  fill: line.color,
                  fontSize: 12,
                }}
              />
            ))}
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
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <table className="visually-hidden">
        <caption>Điểm dự kiến theo tuần</caption>
        <thead>
          <tr>
            <th scope="col">Tuần</th>
            <th scope="col">Điểm dự kiến</th>
          </tr>
        </thead>
        <tbody>
          {data.map((point) => (
            <tr key={point.label}>
              <th scope="row">{point.name}</th>
              <td>{formatDecimal(point.raw)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}

const ASSIGNMENT_COLUMNS = [
  { key: 'code', header: 'Mã', render: (row) => row.code },
  { key: 'name', header: 'Bài tập', rowHeader: true, render: (row) => row.name },
  { key: 'due', header: 'Hạn nộp', render: (row) => formatDay(row.due_date) },
  { key: 'submitted', header: 'Ngày nộp', render: (row) => formatDay(row.submitted_on) },
  { key: 'score', header: 'Điểm', render: (row) => formatDecimal(row.score_10) },
  {
    key: 'status',
    header: 'Trạng thái',
    render: (row) => (
      <span className="lms-status">
        <StatusChip status={`lms_${row.status}`} />
        {row.late && <StatusChip status="lms_late" />}
      </span>
    ),
  },
];

const ASSESSMENT_KIND = { quiz: 'Kiểm tra', midterm: 'Giữa kỳ' };

const ASSESSMENT_COLUMNS = [
  { key: 'kind', header: 'Loại', render: (row) => ASSESSMENT_KIND[row.kind] ?? row.kind },
  { key: 'name', header: 'Bài', rowHeader: true, render: (row) => row.name },
  { key: 'date', header: 'Ngày', render: (row) => formatDay(row.taken_on) },
  { key: 'score', header: 'Điểm', render: (row) => formatDecimal(row.score_10) },
  { key: 'weight', header: 'Trọng số', render: (row) => formatDecimal(row.weight) },
];

function Attendance({ attendance }) {
  return (
    <section aria-labelledby="attendance-title">
      <h2 id="attendance-title" className="section-heading">
        Chuyên cần
      </h2>
      <dl className="detail-list">
        <div>
          <dt>Buổi đã học</dt>
          <dd>
            {formatCount(attendance.held)}
            {attendance.total_sessions ? `/${formatCount(attendance.total_sessions)}` : ''}
          </dd>
        </div>
        <div>
          <dt>Có mặt</dt>
          <dd>{formatCount(attendance.present)}</dd>
        </div>
        <div>
          <dt>Vắng không phép</dt>
          <dd>{formatCount(attendance.absent)}</dd>
        </div>
        <div>
          <dt>Vắng có phép</dt>
          <dd>{formatCount(attendance.excused)}</dd>
        </div>
      </dl>
    </section>
  );
}

function LmsData({ latest }) {
  if (!latest) {
    return <p className="reference-line">Chưa có dữ liệu LMS của môn này.</p>;
  }
  const { summary } = latest;
  return (
    <>
      <section aria-labelledby="lms-scores-title">
        <h2 id="lms-scores-title" className="section-heading">
          Điểm hiện tại từ LMS
          <ScoreHelp />
        </h2>
        <dl className="detail-list">
          <div>
            <dt>{ASSIGNMENT_SCORE}</dt>
            <dd>{formatDecimal(summary.assignment_score)}</dd>
          </div>
          <div>
            <dt>{TEST_SCORE}</dt>
            <dd>{formatDecimal(summary.assessment_average)}</dd>
          </div>
          <div>
            <dt>{PROCESS_SCORE}</dt>
            <dd>{formatDecimal(summary.process_score)}</dd>
          </div>
          <div>
            <dt>Bài đã nộp</dt>
            <dd>
              {formatCount(summary.submitted)}/{formatCount(summary.assignments_total)}
              {summary.overdue > 0 ? ` · ${formatCount(summary.overdue)} quá hạn` : ''}
              {summary.late > 0 ? ` · ${formatCount(summary.late)} nộp muộn` : ''}
            </dd>
          </div>
        </dl>
        <p className="reference-line">
          Dữ liệu LMS tuần {latest.week.week_no} ({formatDay(latest.week.start)}–
          {formatDay(latest.week.end)}), cập nhật ngày {formatDay(latest.as_of)}.
        </p>
      </section>
      <section aria-labelledby="assignments-title" className="stack">
        <h2 id="assignments-title" className="section-heading">
          Bài tập
        </h2>
        <DataTable
          caption="Bài tập của môn"
          columns={ASSIGNMENT_COLUMNS}
          rows={latest.assignments}
          rowKey={(row) => row.code}
        />
      </section>
      <section aria-labelledby="assessments-title" className="stack">
        <h2 id="assessments-title" className="section-heading">
          Bài kiểm tra
        </h2>
        {latest.assessments.length === 0 ? (
          <p>Chưa có bài kiểm tra.</p>
        ) : (
          <DataTable
            caption="Bài kiểm tra của môn"
            columns={ASSESSMENT_COLUMNS}
            rows={latest.assessments}
            rowKey={(row) => row.code}
          />
        )}
      </section>
    </>
  );
}

function Schedule({ data }) {
  const { schedule, latest } = data;
  if (!schedule) {
    return (
      <section aria-labelledby="schedule-title">
        <h2 id="schedule-title" className="section-heading">
          Lịch học
        </h2>
        <p>Môn chưa có lịch học trong kỳ.</p>
      </section>
    );
  }
  const week = schedule.current_week;
  return (
    <section aria-labelledby="schedule-title">
      <h2 id="schedule-title" className="section-heading">
        Lịch học
      </h2>
      <dl className="detail-list">
        <div>
          <dt>Lịch</dt>
          <dd>
            {weekdayName(schedule.weekday)}, buổi đầu {formatDay(schedule.first_session_date)},{' '}
            {formatCount(schedule.total_sessions)} buổi
          </dd>
        </div>
        <div>
          <dt>Tuần hiện tại</dt>
          <dd>
            {week
              ? `Tuần ${week.week_no} (${formatDay(week.start)}–${formatDay(week.end)})`
              : 'Ngoài thời gian học của môn'}
          </dd>
        </div>
        <div>
          <dt>Dữ liệu LMS tới</dt>
          <dd>{latest ? formatDay(latest.as_of) : 'Chưa có'}</dd>
        </div>
      </dl>
    </section>
  );
}

function WeeklyReports({ data, studentId }) {
  const [open, setOpen] = useState(false);
  const summary = data.weekly_reports;
  return (
    <section aria-labelledby="weekly-reports-title">
      <h2 id="weekly-reports-title" className="section-heading">
        Báo cáo tuần
      </h2>
      <p className="weekly-cell">
        <span>{weeklySummaryText(summary)}</span>
        {summary && summary.submitted + summary.missed > 0 && (
          <Button
            variant="ghost"
            size="sm"
            aria-label={`Xem báo cáo tuần môn ${courseCode(data.course.code)}`}
            onClick={() => setOpen(true)}
          >
            Xem
          </Button>
        )}
      </p>
      {open && (
        <WeeklyReportHistory
          studentId={studentId}
          course={data.course}
          onClose={() => setOpen(false)}
        />
      )}
    </section>
  );
}

function CourseDetail({ scope, courseId }) {
  const { search } = useLocation();
  const resource = useApiResource(
    withQuery(`/api/m11/courses/${encodeURIComponent(courseId)}/prediction`, {
      student_id: scope.studentId,
    }),
  );
  const back = (
    <Link className="back-link back-link--mobile" to={`/m11/phan-tich${carrySearch(search)}`}>
      <ArrowLeft size={16} aria-hidden="true" />
      Phân tích &amp; Cảnh báo
    </Link>
  );
  return (
    <div className="stack course-detail">
      {back}
      <ResourceView
        resource={resource}
        loadingText="Đang tải môn học..."
        errorText="Không tải được môn học"
/** Báo tên môn lên đường dẫn phân cấp ở thanh trên cùng (CR-13b). */
function CourseLabel({ name }) {
  usePageLabel(name);
  return null;
}

      >
        {(data) => (
          <div className="stack">
            <PageHeader
              title={data.course.name}
              description={`${courseCode(data.course.code)} · ${formatCount(data.course.credits)} tín chỉ · ${data.semester.name}`}
            />
            <Summary prediction={data.prediction} studentId={scope.studentId} />
            {data.prediction.level !== 'insufficient' && data.prediction.level !== 'barred' && (
              <>
                <Components prediction={data.prediction} />
                <Targets targets={data.prediction.targets} />
              </>
            )}
            <WeeklyChart weekly={data.prediction.weekly} />
            <Attendance attendance={data.prediction.attendance} />
            <LmsData latest={data.latest} />
            <WeeklyReports data={data} studentId={scope.studentId} />
            <Schedule data={data} />
            <Card className="coming-soon-card">
              <h2 className="section-heading">Lộ trình cải thiện – sắp có</h2>
              <p>Gợi ý việc cần làm cho từng môn sẽ có ở bản sau.</p>
            </Card>
            <CourseLabel name={data.course.name} />
            <p className="reference-line">
              {DISCLAIMER} Ngày hệ thống: {formatDay(data.today)}.
            </p>
          </div>
        )}
      </ResourceView>
    </div>
  );
}

export default function CourseDetailPage() {
  const { courseId } = useParams();
  return <M11Page>{(scope) => <CourseDetail scope={scope} courseId={courseId} />}</M11Page>;
}
