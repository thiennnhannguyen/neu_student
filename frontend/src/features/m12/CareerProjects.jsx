import { Check } from 'lucide-react';
import { useState } from 'react';
import { Button, Card, StatusChip } from '../../components/ui';
import EvidencePanel from './evidence/EvidencePanel';
import { chipStatus } from './labels';

const LEVELS = ['Starter', 'Intermediate', 'Job-ready'];

function SelfStudy({ items, note }) {
  if (items.length === 0) {
    return null;
  }
  return (
    <section className="career-self-study" aria-labelledby="career-self-study">
      <h2 id="career-self-study">Tự học ngoài chương trình</h2>
      <p>Không phải học phần chính thức của NEU, không tính vào tiến độ.</p>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      {note && <p className="career-self-study__note">Lưu ý: {note}</p>}
    </section>
  );
}

/**
 * D-318: kỹ năng có bài kiểm tra mô-đun chỉ hiện dấu: đạt thì tick tròn, chưa đạt thì ô vuông trống.
 * Ô vuông chỉ để xem, không phải ô đánh dấu: kỹ năng tự thành "đạt" khi qua bài kiểm tra (quiz
 * ghi minh chứng đã duyệt).
 */
export function QuizMark({ done }) {
  if (done) {
    return (
      <span role="img" aria-label="Đã đạt" title="Đã đạt" className="quiz-mark quiz-mark--done">
        <Check size={16} strokeWidth={3} aria-hidden="true" />
      </span>
    );
  }
  const label = 'Chưa đạt – làm bài kiểm tra ở tab Khung năng lực';
  return <span role="img" aria-label={label} title={label} className="quiz-mark" />;
}

/** Tab Kỹ năng & dự án. Hoàn thành chỉ qua minh chứng được duyệt (R7). */
export default function CareerProjects({
  nodes,
  selfStudy,
  selfStudyNote,
  student,
  onChanged,
  moduleSkillIds = new Set(),
}) {
  const [opened, setOpened] = useState(null);
  const canAct = Boolean(student);
  const evidenceButton = (child) =>
    canAct && (
      <Button variant="ghost" size="sm" onClick={() => setOpened(child)}>
        {student.isStudent && ['not_started', 'rejected'].includes(child.status)
          ? 'Nộp minh chứng'
          : 'Xem minh chứng'}
      </Button>
    );
  const children = nodes.flatMap((node) => node.children);
  const skills = children.filter((child) => child.kind === 'skill');
  const projects = children
    .filter((child) => child.kind === 'project')
    .sort((first, second) => LEVELS.indexOf(first.level) - LEVELS.indexOf(second.level));
  return (
    <>
      {skills.length > 0 && (
        <section aria-labelledby="career-checklist">
          <h2 id="career-checklist">Checklist sẵn sàng thực tập</h2>
          <ul className="career-checklist">
            {skills.map((skill) => (
              <li key={skill.id}>
                <span>{skill.title}</span>
                {moduleSkillIds.has(skill.skill_id) ? (
                  <QuizMark done={skill.status === 'done'} />
                ) : (
                  <span className="career-checklist__actions">
                    <StatusChip status={chipStatus(skill.kind, skill.status)} />
                    {evidenceButton(skill)}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
      {projects.length > 0 && (
        <section aria-labelledby="career-projects">
          <h2 id="career-projects">Dự án portfolio</h2>
          <div className="career-projects">
            {projects.map((project) => (
              <Card as="article" key={project.id} className="career-project">
                <p className="career-project__level">{project.level}</p>
                <h3>{project.title}</h3>
                {project.criteria && <p>{project.criteria}</p>}
                <StatusChip status={chipStatus(project.kind, project.status)} />
                {evidenceButton(project)}
              </Card>
            ))}
          </div>
        </section>
      )}
      <SelfStudy items={selfStudy} note={selfStudyNote} />
      {opened && (
        <EvidencePanel
          child={opened}
          student={student}
          onClose={() => setOpened(null)}
          onChanged={onChanged}
        />
      )}
    </>
  );
}
