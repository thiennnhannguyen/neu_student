import { Card, StatusChip } from '../../components/ui';
import { chipStatus } from './labels';

const LEVELS = ['Starter', 'Intermediate', 'Job-ready'];

function SelfStudy({ items }) {
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
    </section>
  );
}

/** Tab Kỹ năng & dự án. Hoàn thành chỉ qua minh chứng được duyệt (R7). */
export default function CareerProjects({ nodes, selfStudy }) {
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
                <StatusChip status={chipStatus(skill.kind, skill.status)} size="sm" />
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
                <StatusChip status={chipStatus(project.kind, project.status)} size="sm" />
              </Card>
            ))}
          </div>
        </section>
      )}
      <SelfStudy items={selfStudy} />
    </>
  );
}
