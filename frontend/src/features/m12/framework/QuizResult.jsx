import { Award, X } from 'lucide-react';
import CheckBadge from '../../../components/ui/CheckBadge';
import { Button, Card, PageHeader } from '../../../components/ui';
import { SystemTime } from '../../m11/SystemTime';
import InlineCode from './InlineCode';

export function CodeBlock({ code }) {
  return (
    <pre className="quiz-code">
      <code>{code}</code>
    </pre>
  );
}

/** Câu đã nộp: đáp án đúng, lựa chọn của sinh viên, giải thích. Dùng cho kết quả và ôn tập. */
export function ReviewedQuestions({ questions }) {
  return questions.map((question, index) => (
    <Card as="article" key={question.id} className="quiz-question">
      <h2 className="quiz-question__title">
        Câu {index + 1}. <InlineCode text={question.prompt} />
      </h2>
      {question.code && <CodeBlock code={question.code} />}
      <ul className="quiz-review">
        {question.options.map((option) => {
          const chosen = question.selected_option_ids.includes(option.id);
          return (
            <li key={option.id} className={option.is_correct ? 'quiz-review__right' : ''}>
              {option.is_correct ? (
                <CheckBadge size={16} role="img" aria-label="Đáp án đúng" />
              ) : (
                <X size={16} role="img" aria-label="Đáp án sai" />
              )}
              <span>
                <InlineCode text={option.text} />
                {chosen && <strong> (bạn chọn)</strong>}
              </span>
            </li>
          );
        })}
      </ul>
      <p>
        <strong>Giải thích:</strong> <InlineCode text={question.explanation} />
      </p>
    </Card>
  ));
}

export function QuizResult({ result, backTo }) {
  return (
    <section className="quiz-page">
      <PageHeader title={`Kết quả: ${result.module.title}`} />
      <Card className="quiz-result">
        <p className="quiz-result__score">
          {result.correct_count}/{result.total} câu đúng ({result.percent}%)
        </p>
        <p>
          {result.passed
            ? 'Đạt. Kỹ năng của mô-đun đã được tính vào tiến độ nghề.'
            : `Chưa đạt, cần từ ${result.pass_percent}%.`}
        </p>
        {result.auto_submitted && <p>Hết giờ: hệ thống tự nộp theo các đáp án đã lưu.</p>}
        {result.retry_at && (
          <p>
            Làm lại từ <SystemTime iso={result.retry_at} />.
          </p>
        )}
        <div className="module-card__actions">
          {result.certificate && (
            <Button iconLeft={Award} to={`/m12/chung-chi/${result.certificate.code}`}>
              Xem chứng chỉ
            </Button>
          )}
          <Button variant="secondary" to={backTo}>
            Về Khung năng lực
          </Button>
        </div>
      </Card>
      <p className="framework__source">{result.author_label}</p>
      <ReviewedQuestions questions={result.questions} />
    </section>
  );
}
