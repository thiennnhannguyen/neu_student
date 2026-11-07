import { Award, BookOpenCheck, ClipboardCheck } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router';
import { apiRequest } from '../../../api/client';
import { Button, Card, Disclosure, StatusChip, StatusLegend } from '../../../components/ui';
import { courseCode, formatDateTime } from '../../m11/format';
import InlineCode from './InlineCode';

const QUIZ_TEXT = {
  not_started: 'Chưa làm bài kiểm tra',
  in_progress: 'Đang làm dở',
  cooldown: 'Chưa đạt, chờ tới lượt làm lại',
  retry: 'Chưa đạt, có thể làm lại',
  passed: 'Đã đạt',
};

function typeText(course) {
  return `${course.credits} TC · ${course.curriculum_group} · HK ${course.planned_semester}`;
}

function ModuleCard({ module, student, onChanged }) {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const { quiz } = module;

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const attempt = await apiRequest(`/api/m12/modules/${module.id}/attempts`, {
        method: 'POST',
      });
      navigate(`/m12/lam-bai/${attempt.id}`);
    } catch (caught) {
      setError(caught.message);
      setBusy(false);
      onChanged();
    }
  }

  return (
    <Card as="article" className="module-card">
      <p className="module-card__order">Mô-đun {module.order}</p>
      <h3>{module.title}</h3>
      <p className="module-card__progress">
        Môn đã đạt: {module.courses_done}/{module.courses.length}
      </p>
      <p className="module-card__quiz">
        {QUIZ_TEXT[quiz.state]}
        {quiz.state === 'cooldown' && ` (từ ${formatDateTime(quiz.retry_at)})`}
      </p>
      {error && (
        <p role="alert" className="module-card__error">
          {error}
        </p>
      )}
      <div className="module-card__actions">
        {student.isStudent && ['not_started', 'retry'].includes(quiz.state) && (
          <Button iconLeft={ClipboardCheck} onClick={start} disabled={busy}>
            Làm bài kiểm tra
          </Button>
        )}
        {student.isStudent && quiz.state === 'cooldown' && (
          <Button iconLeft={ClipboardCheck} disabled>
            Làm bài kiểm tra
          </Button>
        )}
        {student.isStudent && quiz.state === 'in_progress' && (
          <Button iconLeft={ClipboardCheck} to={`/m12/lam-bai/${quiz.open_attempt_id}`}>
            Làm tiếp
          </Button>
        )}
        {student.isStudent && quiz.can_review && (
          <Button variant="secondary" iconLeft={BookOpenCheck} to={`/m12/on-tap/${module.id}`}>
            Ôn tập
          </Button>
        )}
        {quiz.certificate && (
          <Button
            variant="secondary"
            iconLeft={Award}
            to={student.link(`/m12/chung-chi/${quiz.certificate.code}`)}
          >
            Xem chứng chỉ
          </Button>
        )}
      </div>
      <Disclosure summary="Mục tiêu, môn học, thực hành">
        <h4>Mục tiêu</h4>
        <ul>
          {module.objectives.map((item) => (
            <li key={item}>
              <InlineCode text={item} />
            </li>
          ))}
        </ul>
        <h4>Môn NEU liên quan</h4>
        {module.courses.map((course) => (
          <section key={course.course_id} className="module-card__course">
            <p className="module-card__course-title">
              <StatusChip status={course.status} /> {courseCode(course.code)} {course.name}
            </p>
            <p className="table-note">{typeText(course)}</p>
            <p>
              <strong>Phần cần nắm từ môn này cho Backend:</strong>
            </p>
            <ul>
              {course.takeaways.map((item) => (
                <li key={item}>
                  <InlineCode text={item} />
                </li>
              ))}
            </ul>
          </section>
        ))}
        <h4>Kiến thức bổ sung ngoài CTĐT</h4>
        <ul>
          {module.extra_knowledge.map((item) => (
            <li key={item}>
              <InlineCode text={item} />
            </li>
          ))}
        </ul>
        <h4>Bài thực hành nhỏ</h4>
        <ol>
          {module.practice.map((item) => (
            <li key={item}>
              <InlineCode text={item} />
            </li>
          ))}
        </ol>
      </Disclosure>
    </Card>
  );
}

function Milestones({ rows }) {
  return (
    <section aria-labelledby="framework-milestones">
      <h2 id="framework-milestones">Mốc nghề</h2>
      <div className="framework-milestones">
        {rows.map((row) => (
          <Card as="article" key={row.name}>
            <h3>{row.name}</h3>
            <p>
              Mô-đun đã đạt: {row.modules_done}/{row.modules.length}
            </p>
            <ul>
              {row.modules.map((module) => (
                <li key={module.order}>
                  Mô-đun {module.order}: {module.title}
                </li>
              ))}
            </ul>
            <p>
              <strong>Dự án:</strong> {row.projects.join(', ')}
            </p>
          </Card>
        ))}
      </div>
    </section>
  );
}

function allocationText(allocation) {
  return Object.entries(allocation)
    .map(([semester, credits]) => `HK${semester}: ${credits}`)
    .join(', ');
}

function Electives({ electives }) {
  return (
    <section aria-labelledby="framework-electives">
      <h2 id="framework-electives">Bộ tự chọn đề xuất cho Backend</h2>
      <p>Đề xuất của nhóm biên soạn, trong 15 môn tự chọn của CTĐT. Không bắt buộc.</p>
      <ul className="framework-electives">
        {electives.suggested.map((course) => (
          <li key={course.course_id}>
            <StatusChip status={course.status} /> {courseCode(course.code)} {course.name} (HK{' '}
            {course.planned_semester})
          </li>
        ))}
      </ul>
      <p className="table-note">
        Tín chỉ tự chọn theo học kỳ: bộ đề xuất {allocationText(electives.allocation.suggested)};
        PDF ghi {allocationText(electives.allocation.curriculum)}. Tổng vẫn 30 tín chỉ.
      </p>
      {electives.replaced.length > 0 && (
        <>
          <h3>Môn bạn chọn khác bộ đề xuất</h3>
          <ul>
            {electives.replaced.map((row) => (
              <li key={row.chosen.course_id}>
                {courseCode(row.chosen.code)} {row.chosen.name} thay cho{' '}
                {courseCode(row.instead_of.code)} {row.instead_of.name}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

/** Tab Khung năng lực. Nội dung môn là phần cần nắm do nhóm biên soạn, không phải đề cương. */
export default function CompetencyFramework({ data, student, onChanged }) {
  return (
    <div className="framework">
      <p className="framework__source">
        {data.source}. Câu chữ về từng môn là phần cần nắm cho Backend, không phải đề cương môn học.
      </p>
      <Milestones rows={data.milestones} />
      <section aria-labelledby="framework-modules">
        <h2 id="framework-modules">10 mô-đun năng lực</h2>
        <StatusLegend
          statuses={[
            'done',
            'done_via_equivalency',
            'exempt',
            'in_progress',
            'failed',
            'not_started',
          ]}
        />
        <div className="framework-modules">
          {data.modules.map((module) => (
            <ModuleCard key={module.id} module={module} student={student} onChanged={onChanged} />
          ))}
        </div>
      </section>
      <Electives electives={data.electives} />
    </div>
  );
}
