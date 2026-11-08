/**
 * Màn hình báo cáo tuần toàn trang, "chặn mềm" (CR-12, D-312). Chỉ cho vai trò sinh viên.
 *
 * - Hiện khi đăng nhập hoặc chuyển trang mà còn báo cáo đang mở; nhiều môn làm lần lượt ("Môn 1/2"),
 *   hạn nộp gần nhất trước (thứ tự do API trả).
 * - "Làm sau" dùng một lần cho mỗi báo cáo, lưu ở CSDL. Báo cáo đã "Làm sau" chỉ ẩn trong lần dùng
 *   hiện tại (state của màn hình này); tải lại trang hoặc đăng nhập lại thì hiện lại, không còn nút
 *   "Làm sau" và Esc không đóng.
 * - Không chặn: Đăng xuất, Yêu cầu hỗ trợ (có nút ngay trong màn hình; trang hỗ trợ không hiện).
 * - Bàn phím: focus nằm trong màn hình, phần còn lại của trang bị khóa (inert); đóng thì trả focus.
 */
import { LifeBuoy, LogOut } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router';
import { apiRequest } from '../../api/client';
import { Button, useToast } from '../../components/ui';
import useFocusTrap from '../../components/ui/useFocusTrap';
import { useAuth } from '../auth/AuthContext';
import { courseCode, formatDay } from '../m11/format';
import { NOTE_MAX, PRIVACY_NOTE, QUESTIONS, missingAnswers, reportKey } from './questions';

export const SUPPORT_ROOT = '/m12/yeu-cau-ho-tro';
/** Phần trang bị khóa khi màn hình báo cáo đang hiện (AppLayout gắn thuộc tính này). */
export const INERT_ATTRIBUTE = 'data-report-inert';

function Question({ question, value, error, onChange }) {
  const id = `wr-${question.name}`;
  const describedBy =
    [question.hint ? `${id}-hint` : null, error ? `${id}-error` : null].filter(Boolean).join(' ') ||
    undefined;
  const number = QUESTIONS.indexOf(question) + 1;
  if (question.note) {
    return (
      <div className="weekly-question">
        <label htmlFor={id} className="weekly-question__label">
          {number}. {question.label}
        </label>
        <p id={`${id}-hint`} className="form-field__hint">
          {question.hint}
        </p>
        <textarea
          id={id}
          className="ui-input ui-textarea weekly-question__note"
          rows={2}
          maxLength={NOTE_MAX}
          value={value ?? ''}
          aria-describedby={describedBy}
          onChange={(event) => onChange(event.target.value)}
        />
      </div>
    );
  }
  return (
    <fieldset
      className={`weekly-question${error ? ' weekly-question--error' : ''}`}
      aria-describedby={describedBy}
      aria-invalid={error ? 'true' : undefined}
    >
      <legend className="weekly-question__label">
        {number}. {question.label}
      </legend>
      {question.hint && (
        <p id={`${id}-hint`} className="form-field__hint">
          {question.hint}
        </p>
      )}
      <div className="weekly-question__options">
        {question.options.map((option) => (
          <label key={option.value} className="weekly-option">
            <input
              type="radio"
              name={question.name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
            />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
      {error && (
        <p id={`${id}-error`} className="form-field__error">
          {error}
        </p>
      )}
    </fieldset>
  );
}

function ReportForm({ item, step, total, busy, error, onSubmit, onPostpone, headingRef }) {
  const [answers, setAnswers] = useState({});
  const [missing, setMissing] = useState([]);
  const { week } = item;

  function submit(event) {
    event.preventDefault();
    const gaps = missingAnswers(answers);
    setMissing(gaps);
    if (gaps.length > 0) {
      document.querySelector(`input[name="${gaps[0]}"]`)?.focus();
      return;
    }
    onSubmit(answers);
  }

  return (
    <form className="weekly-report__form" onSubmit={submit} noValidate>
      <p className="weekly-report__step">
        Báo cáo tuần · Môn {step}/{total}
      </p>
      <h2 id="weekly-report-title" ref={headingRef} tabIndex={-1}>
        {courseCode(item.course.code)} – {item.course.name}
      </h2>
      <p className="weekly-report__meta">
        Tuần {week.week_no} ({formatDay(week.start)}–{formatDay(week.end)}) · Hạn nộp hết ngày{' '}
        {formatDay(item.due_on)}
      </p>
      <p className="weekly-report__privacy">{PRIVACY_NOTE}</p>
      {missing.length > 0 && (
        <p role="alert" className="status-error">
          Còn {missing.length} câu chưa trả lời.
        </p>
      )}
      {QUESTIONS.map((question) => (
        <Question
          key={question.name}
          question={question}
          value={answers[question.name]}
          error={missing.includes(question.name) ? 'Chọn một câu trả lời.' : null}
          onChange={(value) => {
            setAnswers((current) => ({ ...current, [question.name]: value }));
            setMissing((current) => current.filter((name) => name !== question.name));
          }}
        />
      ))}
      {error && (
        <p role="alert" className="status-error">
          {error}
        </p>
      )}
      <div className="weekly-report__actions">
        {item.can_postpone ? (
          <Button variant="secondary" disabled={busy} onClick={onPostpone}>
            Làm sau
          </Button>
        ) : (
          <p className="weekly-report__no-postpone">
            Bạn đã chọn “Làm sau” một lần cho báo cáo này.
          </p>
        )}
        <Button type="submit" loading={busy}>
          Nộp báo cáo
        </Button>
      </div>
    </form>
  );
}

function payload(answers) {
  const note = (answers.unclear_note ?? '').trim();
  return { ...answers, unclear_note: note || null };
}

export default function WeeklyReportGate() {
  const { role, logout } = useAuth();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { show } = useToast();
  const [queue, setQueue] = useState([]);
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  // Báo cáo đã "Làm sau" hoặc đã nộp trong lần dùng này: không hiện lại cho tới khi tải lại trang.
  const handled = useRef(new Set());
  const dialogRef = useRef(null);
  const headingRef = useRef(null);
  const isStudent = role === 'student';
  const onSupport = pathname.startsWith(SUPPORT_ROOT);

  // Đăng nhập hoặc chuyển trang: hỏi lại các báo cáo đang mở.
  useEffect(() => {
    if (!isStudent || onSupport) {
      return undefined;
    }
    const controller = new AbortController();
    apiRequest('/api/weekly-reports/open', { signal: controller.signal })
      .then((data) => {
        setQueue(data.items.filter((item) => !handled.current.has(reportKey(item))));
        setStep(0);
        setError('');
      })
      .catch(() => {
        // Không tải được thì không chặn: sinh viên vẫn dùng hệ thống, lần chuyển trang sau thử lại.
      });
    return () => controller.abort();
  }, [isStudent, onSupport, pathname]);

  const item = queue[step];
  const active = Boolean(isStudent && !onSupport && item);

  const next = useCallback(() => {
    handled.current.add(reportKey(item));
    setError('');
    if (step + 1 < queue.length) {
      setStep(step + 1);
    } else {
      setQueue([]);
      setStep(0);
    }
  }, [item, queue.length, step]);

  const postpone = useCallback(async () => {
    if (!item?.can_postpone || busy) {
      return;
    }
    setBusy(true);
    try {
      await apiRequest(`/api/weekly-reports/${item.course.id}/${item.week.week_no}/postpone`, {
        method: 'POST',
      });
      next();
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  }, [busy, item, next]);

  async function submit(answers) {
    setBusy(true);
    try {
      await apiRequest(`/api/weekly-reports/${item.course.id}/${item.week.week_no}/submit`, {
        method: 'POST',
        body: payload(answers),
      });
      show(`Đã nộp báo cáo tuần ${item.week.week_no} môn ${courseCode(item.course.code)}.`);
      next();
    } catch (failure) {
      if (failure.status === 409) {
        // Đã nộp ở nơi khác hoặc vừa quá hạn: báo rồi chuyển sang môn tiếp theo.
        show(failure.message, 'error');
        next();
      } else {
        setError(failure.message);
      }
    } finally {
      setBusy(false);
    }
  }

  // Esc chỉ đóng khi báo cáo còn được "Làm sau"; khi đó Esc giống bấm "Làm sau". useFocusTrap giữ
  // hàm Esc từ lúc bật, nên gọi qua ref để luôn là báo cáo đang hiện.
  const escape = useRef(postpone);
  useEffect(() => {
    escape.current = postpone;
  }, [postpone]);
  useFocusTrap(dialogRef, active, () => escape.current(), headingRef);

  // Khóa phần còn lại của trang khi màn hình báo cáo đang hiện.
  useEffect(() => {
    if (!active) {
      return undefined;
    }
    const blocked = [...document.querySelectorAll(`[${INERT_ATTRIBUTE}]`)];
    blocked.forEach((element) => element.setAttribute('inert', ''));
    return () => blocked.forEach((element) => element.removeAttribute('inert'));
  }, [active]);

  // Sang môn tiếp theo: focus vào tiêu đề môn mới.
  useEffect(() => {
    if (active) {
      headingRef.current?.focus();
    }
  }, [active, step]);

  if (!active) {
    return null;
  }

  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="weekly-report-title"
      className="weekly-report"
    >
      <div className="weekly-report__bar">
        <strong>Báo cáo tuần</strong>
        <div className="weekly-report__exits">
          <Button
            variant="ghost"
            size="sm"
            iconLeft={LifeBuoy}
            onClick={() => navigate(SUPPORT_ROOT)}
          >
            Yêu cầu hỗ trợ
          </Button>
          <Button
            variant="ghost"
            size="sm"
            iconLeft={LogOut}
            onClick={() => logout().catch(() => {})}
          >
            Đăng xuất
          </Button>
        </div>
      </div>
      <div className="weekly-report__body">
        <ReportForm
          key={reportKey(item)}
          item={item}
          step={step + 1}
          total={queue.length}
          busy={busy}
          error={error}
          onSubmit={submit}
          onPostpone={postpone}
          headingRef={headingRef}
        />
      </div>
    </div>
  );
}
