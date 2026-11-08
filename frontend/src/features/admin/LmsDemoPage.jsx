import { Plus, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { apiRequest } from '../../api/client';
import {
  Button,
  Card,
  EmptyState,
  FormField,
  Input,
  PageHeader,
  Select,
  StatusChip,
  useToast,
} from '../../components/ui';
import { formatCount, formatDay, formatDecimal, weekdayName, withQuery } from '../m11/format';
import useApiResource from '../m11/useApiResource';
import { REAL_TIME_NOTE, useDemoToday } from '../m11/SystemTime';
import { ResourceView } from '../m11/ui';
import {
  ASSESSMENT_KINDS,
  ATTENDANCE_OPTIONS,
  attendanceFor,
  draftKey,
  emptyAssessment,
  emptyAssignment,
  formErrors,
  formFromSnapshot,
  readDraft,
  removeDraft,
  toPayload,
  writeDraft,
} from './lmsForm';

const EMPTY_FORM = { attendance: {}, assignments: [], assessments: [] };
const PREVIEW_DELAY_MS = 400;

function storage() {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function fieldErrorText(error) {
  const fields = error?.details?.fields;
  if (!fields) {
    return error?.message ?? '';
  }
  const lines = Object.entries(fields).flatMap(([name, messages]) =>
    (Array.isArray(messages) ? messages : [JSON.stringify(messages)]).map(
      (message) => `${name}: ${message}`,
    ),
  );
  return [error.message, ...lines].join(' ');
}

function AssignmentStatus({ row }) {
  if (!row) {
    return <span className="lms-status__none">—</span>;
  }
  return (
    <span className="lms-status">
      <StatusChip status={`lms_${row.status}`} />
      {row.late && <StatusChip status="lms_late" />}
    </span>
  );
}

function Totals({ preview }) {
  if (preview.status === 'idle') {
    return null;
  }
  if (preview.status === 'error') {
    return (
      <p role="alert" className="status-error">
        {fieldErrorText(preview.error)}
      </p>
    );
  }
  if (preview.status !== 'ok') {
    return (
      <p role="status" className="reference-line">
        Đang tính số tổng...
      </p>
    );
  }
  const { summary, week } = preview.data;
  const completion = summary.completion;
  const rows = [
    ['Tuần của môn', `Tuần ${week.week_no} (${formatDay(week.start)}–${formatDay(week.end)})`],
    ['Buổi đã học', formatCount(summary.sessions_held)],
    ['Vắng', formatCount(summary.absent)],
    ['Vắng có phép', formatCount(summary.excused)],
    ['Bài đã nộp', `${formatCount(summary.submitted)}/${formatCount(summary.assignments_total)}`],
    ['Đã chấm', formatCount(summary.graded)],
    ['Chờ chấm', formatCount(summary.pending)],
    ['Quá hạn chưa nộp', formatCount(summary.overdue)],
    ['Nộp muộn', formatCount(summary.late)],
    [
      '% hoàn thành',
      completion.percent === null
        ? '—'
        : `${completion.percent}% (${completion.numerator}/${completion.denominator} bài đến hạn)`,
    ],
    ['Điểm TB bài tập', formatDecimal(summary.assignment_average)],
    ['Điểm TB kiểm tra', formatDecimal(summary.assessment_average)],
  ];
  return (
    <dl className="detail-list lms-totals" aria-live="polite">
      {rows.map(([name, value]) => (
        <div key={name}>
          <dt>{name}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function AttendanceFieldset({ sessions, attendance, onChange }) {
  if (sessions.length === 0) {
    return <p className="reference-line">Chưa có buổi học nào tới ngày này.</p>;
  }
  return (
    <div className="lms-attendance">
      {sessions.map((session) => (
        <fieldset key={session.session_no} className="lms-attendance__session">
          <legend>
            Buổi {session.session_no} · {formatDay(session.session_date)}
          </legend>
          {ATTENDANCE_OPTIONS.map((option) => (
            <label key={option.value} className="lms-radio">
              <input
                type="radio"
                name={`session-${session.session_no}`}
                value={option.value}
                checked={attendance[session.session_no] === option.value}
                onChange={() => onChange(session.session_no, option.value)}
              />
              {option.label}
            </label>
          ))}
        </fieldset>
      ))}
    </div>
  );
}

function RowField({ id, label, error, children }) {
  return (
    <FormField id={id} label={label} errors={error ? [error] : undefined} className="lms-cell">
      {children}
    </FormField>
  );
}

function AssignmentRows({ rows, errors, statuses, onChange, onRemove }) {
  return rows.map((row, index) => {
    const id = (name) => `assignment-${index}-${name}`;
    const err = (name) => errors[`assignments.${index}.${name}`];
    return (
      <fieldset key={index} className="lms-row">
        <legend>Bài tập {index + 1}</legend>
        <RowField id={id('code')} label="Mã">
          <Input value={row.code} onChange={(e) => onChange(index, 'code', e.target.value)} />
        </RowField>
        <RowField id={id('name')} label="Tên bài">
          <Input value={row.name} onChange={(e) => onChange(index, 'name', e.target.value)} />
        </RowField>
        <RowField id={id('due')} label="Hạn nộp">
          <Input
            type="date"
            value={row.due_date}
            onChange={(e) => onChange(index, 'due_date', e.target.value)}
          />
        </RowField>
        <RowField id={id('submitted')} label="Ngày nộp">
          <Input
            type="date"
            value={row.submitted_on}
            onChange={(e) => onChange(index, 'submitted_on', e.target.value)}
          />
        </RowField>
        <RowField id={id('score')} label="Điểm hệ 10" error={err('score')}>
          <Input
            inputMode="decimal"
            placeholder="vd 7,8"
            value={row.score}
            onChange={(e) => onChange(index, 'score', e.target.value)}
          />
        </RowField>
        <RowField id={id('weight')} label="Trọng số" error={err('weight')}>
          <Input
            inputMode="decimal"
            value={row.weight}
            onChange={(e) => onChange(index, 'weight', e.target.value)}
          />
        </RowField>
        <div className="lms-cell lms-cell--status">
          <span className="lms-cell__label">Trạng thái</span>
          <AssignmentStatus row={statuses?.[index]} />
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onRemove(index)}
          aria-label={`Xóa bài tập ${index + 1}`}
        >
          <Trash2 size={16} aria-hidden="true" />
        </Button>
      </fieldset>
    );
  });
}

function AssessmentRows({ rows, errors, onChange, onRemove }) {
  return rows.map((row, index) => {
    const id = (name) => `assessment-${index}-${name}`;
    const err = (name) => errors[`assessments.${index}.${name}`];
    return (
      <fieldset key={index} className="lms-row lms-row--assessment">
        <legend>Bài kiểm tra {index + 1}</legend>
        <RowField id={id('kind')} label="Loại">
          <Select value={row.kind} onChange={(e) => onChange(index, 'kind', e.target.value)}>
            {ASSESSMENT_KINDS.map((kind) => (
              <option key={kind.value} value={kind.value}>
                {kind.label}
              </option>
            ))}
          </Select>
        </RowField>
        <RowField id={id('code')} label="Mã">
          <Input value={row.code} onChange={(e) => onChange(index, 'code', e.target.value)} />
        </RowField>
        <RowField id={id('name')} label="Tên">
          <Input value={row.name} onChange={(e) => onChange(index, 'name', e.target.value)} />
        </RowField>
        <RowField id={id('date')} label="Ngày làm">
          <Input
            type="date"
            value={row.taken_on}
            onChange={(e) => onChange(index, 'taken_on', e.target.value)}
          />
        </RowField>
        <RowField id={id('score')} label="Điểm hệ 10" error={err('score')}>
          <Input
            inputMode="decimal"
            placeholder="vd 7,8"
            value={row.score}
            onChange={(e) => onChange(index, 'score', e.target.value)}
          />
        </RowField>
        <RowField id={id('weight')} label="Trọng số" error={err('weight')}>
          <Input
            inputMode="decimal"
            value={row.weight}
            onChange={(e) => onChange(index, 'weight', e.target.value)}
          />
        </RowField>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onRemove(index)}
          aria-label={`Xóa bài kiểm tra ${index + 1}`}
        >
          <Trash2 size={16} aria-hidden="true" />
        </Button>
      </fieldset>
    );
  });
}

/** Lấy lịch của môn tới ngày giả lập: tuần của môn và các buổi đã diễn ra (backend tính). */
function useCalendar(studentId, courseId, asOf) {
  const ready = studentId && courseId && /^\d{4}-\d{2}-\d{2}$/.test(asOf);
  return useApiResource(
    ready
      ? withQuery('/api/lms/calendar', { student_id: studentId, course_id: courseId, as_of: asOf })
      : null,
  );
}

function usePreview(payload, enabled) {
  const [state, setState] = useState({ status: 'idle' });
  const body = enabled ? JSON.stringify(payload) : null;
  useEffect(() => {
    if (!body) {
      return undefined;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setState({ status: 'loading' });
      apiRequest('/api/lms/preview', {
        method: 'POST',
        body: JSON.parse(body),
        signal: controller.signal,
      })
        .then((data) => setState({ status: 'ok', data }))
        .catch((error) => {
          if (error.name !== 'AbortError') {
            setState({ status: 'error', error });
          }
        });
    }, PREVIEW_DELAY_MS);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [body]);
  return enabled ? state : { status: 'idle' };
}

function LmsForm({ options }) {
  const { show } = useToast();
  const [studentId, setStudentId] = useState('');
  const [courseId, setCourseId] = useState('');
  const [asOf, setAsOf] = useState(options.today);
  // Bổ sung D-309 (B1): giờ lưu nháp là giờ thật của máy; ghi chú lưu kèm trong bản nháp.
  const realTimeNote = useDemoToday() ? ` ${REAL_TIME_NOTE}` : '';
  const [form, setForm] = useState(EMPTY_FORM);
  const [origin, setOrigin] = useState('');
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState(null);

  const student = options.students.find((row) => row.id === studentId);
  const course = student?.courses.find((row) => row.id === courseId);
  const calendar = useCalendar(studentId, courseId, asOf);
  const week = calendar.status === 'ok' ? calendar.data.week : null;
  const sessions = useMemo(
    () => (calendar.status === 'ok' ? calendar.data.sessions : []),
    [calendar],
  );
  const key = week ? draftKey(studentId, courseId, week.week_no) : null;

  // Đổi môn hoặc tuần: mở bản nháp của tuần đó nếu có, không thì bản đã gửi gần nhất.
  useEffect(() => {
    if (!key) {
      return undefined;
    }
    const draft = readDraft(storage(), key);
    if (draft) {
      setForm({
        attendance: draft.attendance,
        assignments: draft.assignments,
        assessments: draft.assessments,
      });
      setOrigin(`Bản nháp lưu lúc ${draft.savedAt}`);
      return undefined;
    }
    const controller = new AbortController();
    apiRequest(
      withQuery('/api/lms/snapshots/latest', { student_id: studentId, course_id: courseId }),
      { signal: controller.signal },
    )
      .then(({ snapshot }) => {
        if (snapshot) {
          setForm(formFromSnapshot(snapshot));
          setOrigin(`Dữ liệu đã gửi của tuần ${snapshot.week.week_no}`);
        } else {
          setForm(EMPTY_FORM);
          setOrigin('Chưa có dữ liệu đã gửi cho môn này');
        }
      })
      .catch(() => {});
    return () => controller.abort();
  }, [key, studentId, courseId]);

  // Điểm danh luôn đúng các buổi đã diễn ra tới ngày giả lập; buổi mới mặc định "Có mặt".
  const attendance = useMemo(
    () => attendanceFor(sessions, form.attendance),
    [sessions, form.attendance],
  );
  const current = { ...form, attendance };
  const errors = formErrors(current);
  const canPreview = Boolean(week) && Object.keys(errors).length === 0;
  const payload = toPayload({
    studentId,
    courseId,
    asOf,
    form: current,
    sentAt: '1970-01-01T00:00:00Z',
  });
  const preview = usePreview(payload, canPreview);
  const statuses = preview.status === 'ok' ? preview.data.assignments : null;

  function update(listKey, index, field, value) {
    setForm((old) => ({
      ...old,
      [listKey]: old[listKey].map((row, i) => (i === index ? { ...row, [field]: value } : row)),
    }));
  }

  function remove(listKey, index) {
    setForm((old) => ({ ...old, [listKey]: old[listKey].filter((_row, i) => i !== index) }));
  }

  function saveDraft() {
    const savedAt = `${new Date().toLocaleString('vi-VN')}${realTimeNote}`;
    if (writeDraft(storage(), key, current, savedAt)) {
      setOrigin(`Bản nháp lưu lúc ${savedAt}`);
      show('Đã lưu tạm trên trình duyệt này, chưa gửi đi.');
    } else {
      show('Trình duyệt không cho lưu tạm.', 'error');
    }
  }

  async function send() {
    setSending(true);
    setSendError(null);
    try {
      const body = await apiRequest('/api/lms/sync', {
        method: 'POST',
        body: { ...payload, sent_at: new Date().toISOString() },
      });
      removeDraft(storage(), key);
      setForm(formFromSnapshot(body));
      setOrigin(`Dữ liệu đã gửi của tuần ${body.week.week_no}`);
      show(`Đã gửi tuần ${body.week.week_no} của ${course.code} sang hệ thống cảnh báo.`);
    } catch (error) {
      setSendError(error);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="stack lms-form">
      <Card title="Sinh viên và môn học">
        <div className="lms-grid">
          <FormField id="lms-student" label="Sinh viên nhận dữ liệu">
            <Select
              value={studentId}
              onChange={(e) => {
                setStudentId(e.target.value);
                setCourseId('');
              }}
            >
              <option value="">Chọn sinh viên</option>
              {options.students.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.student_code} – {row.full_name}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField id="lms-course" label="Môn đang học kỳ hiện tại">
            <Select
              value={courseId}
              disabled={!student}
              onChange={(e) => setCourseId(e.target.value)}
            >
              <option value="">Chọn môn</option>
              {student?.courses.map((row) => (
                <option key={row.id} value={row.id} disabled={!row.schedule}>
                  {row.code} – {row.name}
                  {row.schedule ? '' : ' (chưa có lịch học)'}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField
            id="lms-as-of"
            label="Giả lập ngày hôm nay"
            hint={
              <>
                {/* Phản hồi CR-11 (B4): ô ngày của trình duyệt theo ngôn ngữ máy, nên ghi thêm dd/mm/yyyy. */}
                <strong className="lms-as-of-text">Ngày đã chọn: {formatDay(asOf)}</strong>
                {' · Chỉ dùng cho lần gửi này, không đổi ngày của hệ thống.'}
              </>
            }
          >
            <Input type="date" value={asOf} onChange={(e) => setAsOf(e.target.value)} />
          </FormField>
        </div>
        {student && (
          <dl className="detail-list lms-identity">
            <div>
              <dt>Mã SV</dt>
              <dd>{student.student_code}</dd>
            </div>
            <div>
              <dt>Họ tên</dt>
              <dd>{student.full_name}</dd>
            </div>
            {course && (
              <>
                <div>
                  <dt>Môn</dt>
                  <dd>
                    {course.code} – {course.name}
                  </dd>
                </div>
                <div>
                  <dt>Lịch học</dt>
                  <dd>
                    {weekdayName(course.schedule.weekday)}, buổi đầu{' '}
                    {formatDay(course.schedule.first_session_date)},{' '}
                    {course.schedule.total_sessions} buổi
                  </dd>
                </div>
              </>
            )}
          </dl>
        )}
      </Card>

      {!course ? (
        <EmptyState
          compact
          title="Chọn sinh viên và môn"
          description="Chỉ có các môn sinh viên đang học ở kỳ hiện tại."
        />
      ) : (
        <ResourceView
          resource={calendar}
          loadingText="Đang tính tuần của môn..."
          errorText="Ngày này chưa nhập được"
          compact
        >
          {() => (
            <>
              <p className="reference-line">{origin}</p>
              <Card title={`Điểm danh tới ngày ${formatDay(asOf)}`}>
                <AttendanceFieldset
                  sessions={sessions}
                  attendance={attendance}
                  onChange={(number, status) =>
                    setForm((old) => ({
                      ...old,
                      attendance: { ...attendance, [number]: status },
                    }))
                  }
                />
              </Card>
              <Card
                title="Bài tập"
                actions={
                  <Button
                    variant="secondary"
                    size="sm"
                    iconLeft={Plus}
                    onClick={() =>
                      setForm((old) => ({
                        ...old,
                        assignments: [
                          ...old.assignments,
                          emptyAssignment(old.assignments.length + 1),
                        ],
                      }))
                    }
                  >
                    Thêm bài tập
                  </Button>
                }
              >
                {form.assignments.length === 0 ? (
                  <p className="reference-line">Chưa có bài tập.</p>
                ) : (
                  <AssignmentRows
                    rows={form.assignments}
                    errors={errors}
                    statuses={statuses}
                    onChange={(i, field, value) => update('assignments', i, field, value)}
                    onRemove={(i) => remove('assignments', i)}
                  />
                )}
              </Card>
              <Card
                title="Bài kiểm tra, giữa kỳ"
                actions={
                  <Button
                    variant="secondary"
                    size="sm"
                    iconLeft={Plus}
                    onClick={() =>
                      setForm((old) => ({
                        ...old,
                        assessments: [
                          ...old.assessments,
                          emptyAssessment(old.assessments.length + 1),
                        ],
                      }))
                    }
                  >
                    Thêm bài kiểm tra
                  </Button>
                }
              >
                {form.assessments.length === 0 ? (
                  <p className="reference-line">Chưa có bài kiểm tra.</p>
                ) : (
                  <AssessmentRows
                    rows={form.assessments}
                    errors={errors}
                    onChange={(i, field, value) => update('assessments', i, field, value)}
                    onRemove={(i) => remove('assessments', i)}
                  />
                )}
              </Card>
              <Card title="Số tổng do hệ thống tính (chỉ đọc)">
                <Totals preview={preview} />
              </Card>
              {sendError && (
                <p role="alert" className="status-error">
                  {fieldErrorText(sendError)}
                </p>
              )}
              <div className="lms-actions">
                <Button variant="secondary" onClick={saveDraft} disabled={!key}>
                  Lưu tạm
                </Button>
                <Button onClick={send} loading={sending} disabled={!canPreview}>
                  Gửi sang hệ thống cảnh báo
                </Button>
              </div>
            </>
          )}
        </ResourceView>
      )}
    </div>
  );
}

/** D-309: form giả lập dữ liệu LMS cho quản trị và cố vấn; gửi đúng API mà LMS thật sẽ gọi. */
export default function LmsDemoPage() {
  const options = useApiResource('/api/lms/form-options');
  return (
    <section className="lms-page">
      <PageHeader
        title="LMS Demo – giả lập dữ liệu LMS"
        description="Dữ liệu nhập ở đây là mô phỏng. Hệ thống tự tính tuần của môn và các số tổng."
      />
      <ResourceView
        resource={options}
        loadingText="Đang tải danh sách sinh viên..."
        errorText="Không tải được danh sách sinh viên"
      >
        {(data) =>
          data.students.length === 0 ? (
            <EmptyState
              title="Chưa có sinh viên"
              description="Không có sinh viên nào trong phạm vi của bạn ở kỳ hiện tại."
            />
          ) : (
            <LmsForm options={data} />
          )
        }
      </ResourceView>
    </section>
  );
}
