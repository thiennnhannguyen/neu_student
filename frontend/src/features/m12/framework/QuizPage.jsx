import { Clock } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router';
import { apiRequest } from '../../../api/client';
import { Button, Card, ConfirmDialog, PageHeader, useToast } from '../../../components/ui';
import { ResourceView } from '../../m11/ui';
import useApiResource from '../../m11/useApiResource';
import InlineCode from './InlineCode';
import { CodeBlock, QuizResult } from './QuizResult';

const CAREER_TAB = '/m12/dinh-huong/nghe/backend-developer?tab=framework';

function clockText(seconds) {
  const minutes = Math.floor(seconds / 60);
  return `${String(minutes).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
}

function useCountdown(initial, onZero) {
  const [left, setLeft] = useState(initial);
  const zero = useRef(onZero);
  zero.current = onZero;
  useEffect(() => {
    const ends = Date.now() + initial * 1000;
    const timer = window.setInterval(() => {
      const next = Math.max(0, Math.ceil((ends - Date.now()) / 1000));
      setLeft(next);
      if (next === 0) {
        window.clearInterval(timer);
        zero.current();
      }
    }, 1000);
    return () => window.clearInterval(timer);
  }, [initial]);
  return left;
}

function QuestionCard({ question, onAnswer, disabled }) {
  const multiple = question.kind === 'multi';
  const name = `question-${question.id}`;
  function change(optionId, checked) {
    if (!multiple) {
      onAnswer(question.id, [optionId]);
      return;
    }
    const rest = question.selected_option_ids.filter((id) => id !== optionId);
    onAnswer(question.id, checked ? [...rest, optionId] : rest);
  }
  return (
    <Card as="article" className="quiz-question">
      <fieldset disabled={disabled}>
        <legend>
          Câu {question.order}. <InlineCode text={question.prompt} />
        </legend>
        {question.code && <CodeBlock code={question.code} />}
        {multiple && <p className="table-note">Chọn tất cả đáp án đúng.</p>}
        {question.options.map((option) => (
          <label key={option.id} className="quiz-option">
            <input
              type={multiple ? 'checkbox' : 'radio'}
              name={name}
              checked={question.selected_option_ids.includes(option.id)}
              onChange={(event) => change(option.id, event.target.checked)}
            />
            <span>
              <InlineCode text={option.text} />
            </span>
          </label>
        ))}
      </fieldset>
    </Card>
  );
}

function OpenAttempt({ attempt, onFinished }) {
  const { show } = useToast();
  const [questions, setQuestions] = useState(attempt.questions);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const saving = useRef(Promise.resolve());

  const submit = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      await saving.current;
      onFinished(await apiRequest(`/api/m12/attempts/${attempt.id}/submit`, { method: 'POST' }));
    } catch (caught) {
      if (caught.code === 'ATTEMPT_CLOSED') {
        onFinished(await apiRequest(`/api/m12/attempts/${attempt.id}`));
        return;
      }
      setError(caught.message);
      setBusy(false);
    }
  }, [attempt.id, onFinished]);

  const left = useCountdown(attempt.remaining_seconds, submit);

  function answer(questionId, optionIds) {
    setQuestions((rows) =>
      rows.map((row) => (row.id === questionId ? { ...row, selected_option_ids: optionIds } : row)),
    );
    saving.current = saving.current
      .then(() =>
        apiRequest(`/api/m12/attempts/${attempt.id}/answers/${questionId}`, {
          method: 'PUT',
          body: { option_ids: optionIds },
        }),
      )
      .catch((caught) => show(`Không lưu được đáp án: ${caught.message}`));
  }

  const answered = questions.filter((row) => row.selected_option_ids.length > 0).length;
  return (
    <>
      <PageHeader title={`Bài kiểm tra: ${attempt.module.title}`} />
      <div className="quiz-bar" role="status">
        <span className="quiz-bar__clock" aria-label={`Thời gian còn lại ${clockText(left)}`}>
          <Clock size={16} aria-hidden="true" /> {clockText(left)}
        </span>
        <span>
          Đã trả lời {answered}/{questions.length}
        </span>
      </div>
      <p className="framework__source">{attempt.author_label}. Đáp án được lưu mỗi lần bạn chọn.</p>
      {questions.map((question) => (
        <QuestionCard key={question.id} question={question} onAnswer={answer} disabled={busy} />
      ))}
      {error && (
        <p role="alert" className="module-card__error">
          {error}
        </p>
      )}
      <Button onClick={() => setConfirming(true)} disabled={busy}>
        Nộp bài
      </Button>
      {confirming && (
        <ConfirmDialog
          title="Nộp bài kiểm tra?"
          confirmLabel="Nộp bài"
          busy={busy}
          onConfirm={submit}
          onCancel={() => setConfirming(false)}
        >
          Đã trả lời {answered}/{questions.length} câu. Nộp rồi thì không sửa được.
        </ConfirmDialog>
      )}
    </>
  );
}

export default function QuizPage() {
  const { attemptId } = useParams();
  const resource = useApiResource(`/api/m12/attempts/${attemptId}`);
  const [finished, setFinished] = useState(null);
  if (finished) {
    return <QuizResult result={finished} backTo={CAREER_TAB} />;
  }
  return (
    <section className="quiz-page">
      {resource.status !== 'ok' && <PageHeader title="Bài kiểm tra" />}
      <ResourceView
        resource={resource}
        loadingText="Đang tải bài kiểm tra..."
        errorText="Không tải được bài kiểm tra"
      >
        {(data) =>
          data.status === 'in_progress' ? (
            <OpenAttempt attempt={data} onFinished={setFinished} />
          ) : (
            <QuizResult result={data} backTo={CAREER_TAB} />
          )
        }
      </ResourceView>
    </section>
  );
}
