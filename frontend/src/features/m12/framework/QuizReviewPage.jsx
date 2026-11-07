import { useParams } from 'react-router';
import { Button, PageHeader } from '../../../components/ui';
import { ResourceView } from '../../m11/ui';
import useApiResource from '../../m11/useApiResource';
import { ReviewedQuestions } from './QuizResult';

/** Ôn tập: xem lại câu đã làm và giải thích, không chấm. */
export default function QuizReviewPage() {
  const { moduleId } = useParams();
  const resource = useApiResource(`/api/m12/modules/${moduleId}/review`);
  return (
    <section className="quiz-page">
      <PageHeader
        title={resource.status === 'ok' ? `Ôn tập: ${resource.data.module.title}` : 'Ôn tập'}
        actions={
          <Button variant="secondary" to="/m12/dinh-huong/nghe/backend-developer?tab=framework">
            Về Khung năng lực
          </Button>
        }
      />
      <ResourceView
        resource={resource}
        loadingText="Đang tải câu hỏi..."
        errorText="Không tải được câu hỏi"
      >
        {(data) => (
          <>
            <p className="framework__source">
              {data.author_label}. Phần này không chấm điểm, không tính lượt làm bài.
            </p>
            <ReviewedQuestions questions={data.questions} />
          </>
        )}
      </ResourceView>
    </section>
  );
}
