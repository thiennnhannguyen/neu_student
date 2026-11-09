import { ArrowLeft, ClipboardCheck, ExternalLink, Route as RouteIcon } from 'lucide-react';
import { Link, useParams } from 'react-router';
import { Button, EmptyState, ErrorState, PageHeader } from '../../../components/ui';
import { useAuth } from '../../auth/AuthContext';
import { courseCode, withQuery } from '../../m11/format';
import useApiResource from '../../m11/useApiResource';
import { ResourceView } from '../../m11/ui';
import CareerIllustration from '../illustrations/CareerIllustration';
import { groupLabel } from '../labels';
import ProgressRing from '../ProgressRing';
import SetGoalButton from '../SetGoalButton';
import useCareerStudent from '../useCareerStudent';

const DETAIL_READERS = new Set(['student', 'advisor', 'admin']);
export const UPDATING_TITLE = 'Đang cập nhật';

/** Mục lục và id của từng phần; phần "Bạn đang ở đâu" chỉ có với sinh viên. */
const SECTIONS = [
  { id: 'gioi-thieu', label: 'Giới thiệu' },
  { id: 'mot-ngay', label: 'Một ngày làm việc' },
  { id: 'so-sanh', label: 'So sánh nghề' },
  { id: 'ky-nang', label: 'Kỹ năng cần có' },
  { id: 'hoc-o-neu', label: 'Học ở NEU' },
  { id: 'san-pham', label: 'Sản phẩm nên có' },
  { id: 'thu-nhap', label: 'Thu nhập tham khảo' },
  { id: 'hoi-dap', label: 'Câu hỏi thường gặp' },
  { id: 'ban-o-dau', label: 'Bạn đang ở đâu', studentOnly: true },
  { id: 'buoc-tiep-theo', label: 'Bước tiếp theo' },
  { id: 'nguon', label: 'Nguồn' },
];

function detailPath(slug) {
  return `/m12/dinh-huong/nghe/${slug}`;
}

/** Mã nguồn của từng ý, bấm vào thì tới dòng nguồn ở cuối trang. */
function Sources({ ids }) {
  if (!ids?.length) {
    return null;
  }
  return (
    <span className="landing-source">
      Nguồn:{' '}
      {ids.map((id, index) => (
        <span key={id}>
          {index > 0 && ', '}
          <a href={`#nguon-${id}`}>{id}</a>
        </span>
      ))}
    </span>
  );
}

function Section({ id, title, children }) {
  return (
    <section id={id} className="landing-section" aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`}>{title}</h2>
      {children}
    </section>
  );
}

function Intro({ career, content }) {
  return (
    <section id="gioi-thieu" className="landing-intro" aria-labelledby="landing-title">
      <div className="landing-intro__media">
        <CareerIllustration illustrationKey={career.illustration_key} />
      </div>
      <div className="landing-intro__body">
        <p className="landing-intro__group">{groupLabel(career.group)}</p>
        <h1 id="landing-title">{career.display_name}</h1>
        <p className="landing-intro__en">{career.name_en}</p>
        <p className="landing-intro__summary">{content.intro.summary}</p>
        <Sources ids={content.intro.sources} />
      </div>
    </section>
  );
}

function Workday({ block }) {
  return (
    <Section id="mot-ngay" title={block.title}>
      <p className="landing-note">{block.note}</p>
      <ol className="landing-list">
        {block.items.map((item) => (
          <li key={item.text}>
            <p>{item.text}</p>
            <Sources ids={item.sources} />
          </li>
        ))}
      </ol>
    </Section>
  );
}

function Comparison({ block }) {
  return (
    <Section id="so-sanh" title={block.title}>
      <div
        className="landing-table-wrap"
        role="region"
        aria-label="Bảng so sánh, cuộn ngang được"
        // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- cuộn ngang bằng bàn phím
        tabIndex={0}
      >
        <table className="landing-table landing-table--compare">
          <caption className="visually-hidden">{block.title}</caption>
          <thead>
            <tr>
              <th scope="col">Tiêu chí</th>
              {block.careers.map((career) => (
                <th key={career.slug} scope="col">
                  {career.name_en}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row) => (
              <tr key={row.label}>
                <th scope="row">
                  {row.label}
                  <Sources ids={row.sources} />
                </th>
                {row.cells.map((cell, index) => (
                  <td key={block.careers[index].slug}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="landing-note landing-note--hint">
        Trên màn hình hẹp, vuốt ngang bảng để xem đủ 4 nghề.
      </p>
    </Section>
  );
}

function Modules({ block, modules, moduleLink }) {
  return (
    <Section id="ky-nang" title={block.title}>
      <p className="landing-note">{block.intro}</p>
      <ol className="landing-modules">
        {modules.map((module) => (
          <li key={module.id}>
            <span className="landing-modules__order">Mô-đun {module.order}</span>
            {moduleLink ? (
              <Link to={moduleLink(module.order)} className="landing-modules__title">
                {module.title}
              </Link>
            ) : (
              <strong className="landing-modules__title">{module.title}</strong>
            )}
            <span className="landing-modules__summary">{module.summary}</span>
          </li>
        ))}
      </ol>
    </Section>
  );
}

function Courses({ block, stages, program }) {
  return (
    <Section id="hoc-o-neu" title={`${block.title} (${program.code})`}>
      <p className="landing-note">{block.intro}</p>
      <ol className="landing-stages">
        {stages.map((stage) => (
          <li key={stage.id} className="landing-stage">
            <h3>
              Giai đoạn {stage.order}. {stage.name}
            </h3>
            {stage.deliverable && (
              <p className="landing-stage__deliverable">
                <strong>Sản phẩm cần đạt: </strong>
                {stage.deliverable}
              </p>
            )}
            {stage.courses.length > 0 ? (
              <ul className="landing-courses">
                {stage.courses.map((course) => (
                  <li key={course.course_id}>
                    <span className="landing-courses__name">
                      <span className="landing-courses__code">{courseCode(course.code)}</span>{' '}
                      {course.name}
                    </span>
                    <span className="landing-courses__meta">
                      <abbr title={course.requirement_type === 'required' ? 'Bắt buộc' : 'Tự chọn'}>
                        {course.type_label}
                      </abbr>{' '}
                      · HK {course.planned_semester} · {course.credits} tín chỉ
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="landing-note">Giai đoạn này là dự án, không có môn học riêng.</p>
            )}
          </li>
        ))}
      </ol>
      <p className="landing-note">{block.semester_note}</p>
      <p className="landing-note">{block.other_programs_note}</p>
      <Sources ids={block.sources} />
    </Section>
  );
}

function Projects({ block, moduleLink }) {
  return (
    <Section id="san-pham" title={block.title}>
      <ul className="landing-projects">
        {block.items.map((item) => (
          <li key={item.name} className="landing-project">
            <p className="landing-project__level">{item.level}</p>
            <h3>{item.name}</h3>
            <p>{item.summary}</p>
            <p className="landing-project__skills-title">Kỹ năng chứng minh:</p>
            <ul className="landing-project__skills">
              {item.modules.map((module) => (
                <li key={module.order}>
                  {moduleLink ? (
                    <Link to={moduleLink(module.order)}>
                      Mô-đun {module.order}: {module.title}
                    </Link>
                  ) : (
                    `Mô-đun ${module.order}: ${module.title}`
                  )}
                </li>
              ))}
            </ul>
            <Sources ids={item.sources} />
          </li>
        ))}
      </ul>
    </Section>
  );
}

function Income({ block }) {
  const { source } = block;
  return (
    <Section id="thu-nhap" title={block.title}>
      <p className="landing-income__caveat">{block.caveat}</p>
      <div className="landing-income">
        <table className="landing-table landing-income__table">
          <caption className="visually-hidden">{block.title}</caption>
          <thead>
            <tr>
              <th scope="col">{block.experience_label}</th>
              <th scope="col" className="landing-table__number">
                {block.amount_label}
              </th>
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row) => (
              <tr key={row.experience}>
                <th scope="row">{row.experience}</th>
                <td className="landing-table__number">{row.amount}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="landing-income__levels">
          <h3>{block.levels_title}</h3>
          <ol>
            {block.levels.map((level) => (
              <li key={level}>{level}</li>
            ))}
          </ol>
        </div>
      </div>
      <p className="landing-note">{block.note}</p>
      <p className="landing-note">
        Nguồn: {source.publisher},{' '}
        <a href={source.url} target="_blank" rel="noopener noreferrer">
          “{source.title}”
          <ExternalLink size={14} aria-hidden="true" className="landing-external" />
          <span className="visually-hidden"> (mở tab mới)</span>
        </a>
        , {source.author}, {source.published}.
      </p>
    </Section>
  );
}

function Faq({ block }) {
  return (
    <Section id="hoi-dap" title={block.title}>
      <div className="landing-faq">
        {block.items.map((item) => (
          <div key={item.question} className="landing-faq__item">
            <h3>{item.question}</h3>
            <p>{item.answer}</p>
            <Sources ids={item.sources} />
          </div>
        ))}
      </div>
    </Section>
  );
}

function nextModule(modules) {
  return modules.find((module) => module.quiz.state !== 'passed') ?? null;
}

/** Chỉ sinh viên: gọi lại 3 API sẵn có, không tính lại ở đây. */
function StudentProgress({ title, frameworkResource, progressResource, certificates }) {
  return (
    <Section id="ban-o-dau" title={title}>
      <ResourceView
        resource={progressResource}
        loadingText="Đang tải tiến độ..."
        errorText="Không tải được tiến độ"
        compact
      >
        {(progress) => (
          <div className="landing-progress">
            <div className="landing-progress__rings">
              <ProgressRing percent={progress.course_progress.percent} label="Học phần" />
              <ProgressRing percent={progress.skill_progress.percent} label="Kỹ năng & dự án" />
            </div>
            <ul className="landing-progress__facts">
              <li>
                Học phần: {progress.course_progress.numerator}/
                {progress.course_progress.denominator} môn đã đạt
              </li>
              <li>
                Kỹ năng &amp; dự án: {progress.skill_progress.numerator}/
                {progress.skill_progress.denominator} đã có minh chứng được duyệt
              </li>
              <FrameworkFacts resource={frameworkResource} certificates={certificates} />
            </ul>
            <p className="landing-note">{progress.disclaimer}.</p>
          </div>
        )}
      </ResourceView>
    </Section>
  );
}

function FrameworkFacts({ resource, certificates }) {
  if (resource.status === 'error') {
    return <li>Không tải được khung năng lực.</li>;
  }
  if (resource.status !== 'ok' || certificates.status === 'loading') {
    return <li>Đang tải khung năng lực...</li>;
  }
  const { modules } = resource.data;
  if (modules.length === 0) {
    return <li>Ngành của bạn chưa có khung năng lực cho nghề này.</li>;
  }
  const next = nextModule(modules);
  const ids = new Set(modules.map((module) => module.id));
  const count =
    certificates.status === 'ok'
      ? certificates.data.items.filter((item) => item.valid && ids.has(item.module_id)).length
      : null;
  return (
    <>
      <li>
        Mô-đun tiếp theo nên làm bài kiểm tra:{' '}
        {next ? `Mô-đun ${next.order} – ${next.title}` : 'đã đạt cả 10 mô-đun'}
      </li>
      <li>
        Chứng chỉ mô-đun đã có: {count === null ? 'không tải được' : `${count}/${modules.length}`}
      </li>
    </>
  );
}

function Actions({ title, career, isStudent, progressResource, frameworkResource, links }) {
  const progress = progressResource.status === 'ok' ? progressResource.data : null;
  const modules = frameworkResource.status === 'ok' ? frameworkResource.data.modules : [];
  const next = nextModule(modules);
  return (
    <Section id="buoc-tiep-theo" title={title}>
      <div className="landing-actions">
        {isStudent && progress && !progress.is_primary && (
          <SetGoalButton
            career={{ id: career.id, name: career.display_name }}
            onChanged={progressResource.retry}
            label="Đặt làm mục tiêu"
          />
        )}
        {links && (
          <Button iconLeft={RouteIcon} to={links.roadmap}>
            Xem lộ trình học
          </Button>
        )}
        {isStudent && next && links && (
          <Button variant="secondary" iconLeft={ClipboardCheck} to={links.module(next.order)}>
            Làm bài kiểm tra mô-đun tiếp theo
          </Button>
        )}
      </div>
    </Section>
  );
}

function SourceList({ sources, income }) {
  return (
    <Section id="nguon" title="Nguồn">
      <ul className="landing-sources">
        {sources.map((source) => (
          <li key={source.id} id={`nguon-${source.id}`}>
            <strong>{source.id}</strong> {source.title}. {source.section}.
          </li>
        ))}
        <li>
          <strong>Thu nhập tham khảo</strong> {income.source.publisher}, “{income.source.title}”,{' '}
          {income.source.author}, {income.source.published}.
        </li>
      </ul>
    </Section>
  );
}

function Toc({ isStudent }) {
  return (
    <nav className="landing-toc" aria-label="Mục lục trang">
      <p className="landing-toc__title">Trên trang này</p>
      <ol>
        {SECTIONS.filter((item) => isStudent || !item.studentOnly).map((item) => (
          <li key={item.id}>
            <a href={`#${item.id}`}>{item.label}</a>
          </li>
        ))}
      </ol>
    </nav>
  );
}

function Landing({ slug, data, student, canOpenDetail }) {
  const { career, landing } = data;
  const { content } = landing;
  const progress = useApiResource(
    student.isStudent ? `/api/m12/progress/careers/slug/${slug}` : null,
  );
  const framework = useApiResource(
    student.isStudent ? `/api/m12/careers/slug/${slug}/framework` : null,
  );
  const certificates = useApiResource(student.isStudent ? '/api/m12/certificates' : null);
  const links = canOpenDetail
    ? {
        roadmap: withQuery(detailPath(slug), { student: student.studentId, tab: 'roadmap' }),
        module: (order) =>
          `${withQuery(detailPath(slug), { student: student.studentId, tab: 'framework' })}#module-${order}`,
      }
    : null;
  return (
    <div className="landing-layout">
      <Toc isStudent={student.isStudent} />
      <div className="landing-main">
        <Intro career={career} content={content} />
        <Workday block={content.workday} />
        <Comparison block={content.comparison} />
        <Modules block={content.modules} modules={landing.modules} moduleLink={links?.module} />
        <Courses block={content.courses} stages={landing.stages} program={landing.program} />
        <Projects block={content.projects} moduleLink={links?.module} />
        <Income block={content.income} />
        <Faq block={content.faq} />
        {student.isStudent && (
          <StudentProgress
            title={content.progress.title}
            progressResource={progress}
            frameworkResource={framework}
            certificates={certificates}
          />
        )}
        <Actions
          title={content.actions.title}
          career={career}
          isStudent={student.isStudent}
          progressResource={progress}
          frameworkResource={framework}
          links={links}
        />
        <SourceList sources={landing.sources} income={content.income} />
      </div>
    </div>
  );
}

export default function CareerLandingPage() {
  const { slug } = useParams();
  const { role } = useAuth();
  const student = useCareerStudent();
  const canOpenDetail = DETAIL_READERS.has(role);
  const resource = useApiResource(`/api/m12/careers/slug/${slug}/landing`);
  const back = canOpenDetail
    ? { to: student.link(detailPath(slug)), label: 'Quay lại trang nghề' }
    : { to: '/', label: 'Về trang chủ' };
  const backButton = (
    <Button variant="ghost" iconLeft={ArrowLeft} to={back.to} className="landing-back">
      {back.label}
    </Button>
  );
  if (resource.status === 'error' && resource.error.status === 404) {
    return (
      <section className="m12-page landing-page">
        {backButton}
        <EmptyState
          heading="h1"
          title="Không tìm thấy nghề"
          description="Đường dẫn không khớp với nghề nào đang công bố."
        />
      </section>
    );
  }
  return (
    <section className="m12-page landing-page">
      {backButton}
      {resource.status === 'error' ? (
        <>
          <PageHeader title="Giới thiệu nghề" />
          <ErrorState
            title="Không tải được trang giới thiệu nghề"
            description={resource.error.message}
            onRetry={resource.retry}
          />
        </>
      ) : (
        <ResourceView resource={resource} loadingText="Đang tải trang giới thiệu nghề...">
          {(data) =>
            data.landing ? (
              <Landing slug={slug} data={data} student={student} canOpenDetail={canOpenDetail} />
            ) : (
              <>
                <PageHeader title={data.career.display_name} />
                <EmptyState
                  title={UPDATING_TITLE}
                  description="Trang giới thiệu của nghề này đang được biên soạn."
                />
              </>
            )
          }
        </ResourceView>
      )}
    </section>
  );
}
