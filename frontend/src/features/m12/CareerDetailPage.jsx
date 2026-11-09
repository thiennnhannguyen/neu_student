import { CalendarRange } from 'lucide-react';
import { useRef, useState } from 'react';
import { Navigate, useParams, useSearchParams } from 'react-router';
import { Button, EmptyState, PageHeader, Tabs } from '../../components/ui';
import { withQuery } from '../m11/format';
import useApiResource from '../m11/useApiResource';
import { DataWarnings, ResourceView } from '../m11/ui';
import CareerCourses from './CareerCourses';
import CareerHero from './CareerHero';
import CareerProjects from './CareerProjects';
import CareerRoadmap from './CareerRoadmap';
import { PICK_STUDENT_HINT } from './CareersPage';
import CompetencyFramework from './framework/CompetencyFramework';
import { K68_NOTE, NOT_RECRUITMENT } from './labels';
import RequirementPanel from './RequirementPanel';
import SetGoalButton from './SetGoalButton';
import useCareerStudent from './useCareerStudent';
import useMediaQuery from './useMediaQuery';

const OLD_ID_PREFIX = 'career-';
const PUSH_PANEL_QUERY = '(min-width: 1280px)';

function Detail({ student, data, reload, slug }) {
  const [selected, setSelected] = useState(null);
  const [params] = useSearchParams();
  const framework = useApiResource(
    withQuery(`/api/m12/careers/slug/${slug}/framework`, student.query),
  );
  // Tải lại khung năng lực thì giữ dữ liệu cũ, để tab và thông báo lỗi không bị dựng lại.
  const shownFramework = useRef(null);
  if (framework.status === 'ok') {
    shownFramework.current = framework.data;
  }
  const modules = shownFramework.current?.modules ?? [];
  const pushes = useMediaQuery(PUSH_PANEL_QUERY);
  const { profile, nodes } = data;
  const tabs = [
    {
      id: 'roadmap',
      label: 'Lộ trình học',
      content: (
        <CareerRoadmap
          label={`Lộ trình ${profile.display_name}`}
          nodes={nodes}
          onSelect={setSelected}
        />
      ),
    },
    {
      id: 'courses',
      label: 'Môn học NEU',
      content: <CareerCourses nodes={nodes} onSelect={setSelected} />,
    },
    {
      id: 'skills',
      label: 'Kỹ năng & dự án',
      content: (
        <CareerProjects
          nodes={nodes}
          selfStudy={profile.self_study}
          selfStudyNote={profile.self_study_note}
          student={student}
          onChanged={reload}
          moduleSkillIds={new Set(modules.map((module) => module.skill_id))}
        />
      ),
    },
    ...(modules.length > 0
      ? [
          {
            id: 'framework',
            label: 'Khung năng lực',
            content: (
              <CompetencyFramework
                data={shownFramework.current}
                student={student}
                onChanged={framework.retry}
              />
            ),
          },
        ]
      : []),
  ];
  return (
    <>
      <CareerHero
        profile={profile}
        isPrimary={data.is_primary}
        fit={data.fits_major}
        progress={{
          course: data.course_progress,
          skill: data.skill_progress,
          coverage: data.coverage,
          disclaimer: data.disclaimer,
        }}
        action={
          <div className="career-hero__actions">
            {student.isStudent && !data.is_primary && (
              <SetGoalButton
                career={{ id: data.career.id, name: profile.display_name }}
                onChanged={reload}
              />
            )}
            {data.is_primary && (
              <Button
                variant="secondary"
                iconLeft={CalendarRange}
                to={student.link('/m12/ke-hoach')}
              >
                Xem lộ trình theo học kỳ
              </Button>
            )}
          </div>
        }
      />
      <DataWarnings warnings={data.data_warnings} />
      <div className={`career-detail${selected && pushes ? ' career-detail--with-panel' : ''}`}>
        <div className="career-detail__main">
          <Tabs
            // Tab Khung năng lực có sau khi tải xong: dựng lại để mở đúng tab theo đường dẫn.
            key={modules.length > 0 ? 'with-framework' : 'plain'}
            tabs={tabs}
            label="Nội dung nghề"
            idPrefix="career"
            initial={params.get('tab')}
          />
        </div>
        {selected && (
          <RequirementPanel
            key={selected.id}
            child={selected}
            link={student.link}
            inline={pushes}
            onClose={() => setSelected(null)}
          />
        )}
      </div>
      <p className="career-disclaimer">{NOT_RECRUITMENT}.</p>
      {profile.major_fit && (
        <p className="career-disclaimer">{shownFramework.current?.program_note ?? K68_NOTE}</p>
      )}
    </>
  );
}

export default function CareerDetailPage() {
  const { slug } = useParams();
  const student = useCareerStudent();
  const isOldLink = slug.startsWith(OLD_ID_PREFIX);
  const last = useRef(null);
  const resource = useApiResource(
    student.needsStudent || isOldLink
      ? null
      : withQuery(`/api/m12/progress/careers/slug/${slug}`, student.query),
  );
  if (isOldLink) {
    return (
      <Navigate
        replace
        to={student.link(`/m12/dinh-huong/nghe/${slug.slice(OLD_ID_PREFIX.length)}`)}
      />
    );
  }
  if (student.needsStudent) {
    return (
      <section className="m12-page">
        <PageHeader title="Chi tiết nghề" />
        <EmptyState title="Chưa chọn sinh viên" description={PICK_STUDENT_HINT} />
      </section>
    );
  }
  // Tải lại sau thao tác (đặt mục tiêu, nộp minh chứng) thì giữ nguyên trang và tab đang mở.
  if (resource.status === 'ok') {
    last.current = { slug, data: resource.data };
  }
  const shown =
    resource.status === 'loading' && last.current?.slug === slug
      ? { status: 'ok', data: last.current.data, retry: resource.retry }
      : resource;
  return (
    <section className="m12-page">
      {shown.status !== 'ok' && <PageHeader title="Chi tiết nghề" />}
      <ResourceView resource={shown} loadingText="Đang tải nghề..." errorText="Không tải được nghề">
        {(data) => (
          <Detail key={slug} slug={slug} student={student} data={data} reload={resource.retry} />
        )}
      </ResourceView>
    </section>
  );
}
