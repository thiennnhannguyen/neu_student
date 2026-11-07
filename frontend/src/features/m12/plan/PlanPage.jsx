import { AlertTriangle, GitCompare, RefreshCw } from 'lucide-react';
import { useState } from 'react';
import { apiRequest } from '../../../api/client';
import {
  Badge,
  Button,
  ConfirmDialog,
  Disclosure,
  EmptyState,
  PageHeader,
  useToast,
} from '../../../components/ui';
import { withQuery } from '../../m11/format';
import useApiResource from '../../m11/useApiResource';
import { ResourceView } from '../../m11/ui';
import { PICK_STUDENT_HINT } from '../CareersPage';
import CareerIllustration from '../illustrations/CareerIllustration';
import useCareerStudent from '../useCareerStudent';
import useMediaQuery from '../useMediaQuery';
import {
  CURRENT_API,
  NO_OFFERING_DATA,
  offeringSummary,
  OUTSIDE_NOTE,
  OUTSIDE_TITLE,
  REGENERATE_WARNING,
} from './labels';
import PlanItemCard from './PlanItemCard';
import PlanPanel from './PlanPanel';

const GENERATE = '/api/m12/roadmaps/generate';

function GenerateButton({ hasRoadmap, onDone }) {
  const { show } = useToast();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function run() {
    setBusy(true);
    setError('');
    try {
      await apiRequest(GENERATE, { method: 'POST', body: {} });
      setOpen(false);
      show('Đã tạo lộ trình mới.');
      onDone();
    } catch (cause) {
      setError(cause.message);
    } finally {
      setBusy(false);
    }
  }

  if (!hasRoadmap) {
    return (
      <>
        <Button loading={busy} onClick={run}>
          Tạo lộ trình
        </Button>
        {error && (
          <p role="alert" className="status-error">
            {error}
          </p>
        )}
      </>
    );
  }
  return (
    <>
      <Button variant="secondary" iconLeft={RefreshCw} onClick={() => setOpen(true)}>
        Tạo lại
      </Button>
      {open && (
        <ConfirmDialog
          title="Tạo lại lộ trình?"
          confirmLabel="Tạo lại"
          busy={busy}
          error={error}
          onConfirm={run}
          onCancel={() => setOpen(false)}
        >
          <p>{REGENERATE_WARNING}. Bản hiện tại được lưu lại trong lịch sử phiên bản.</p>
        </ConfirmDialog>
      )}
    </>
  );
}

function PlanHeader({ roadmap, student, onDone }) {
  const { career, totals } = roadmap;
  return (
    <div className="plan-head">
      <span className="plan-head__media">
        <CareerIllustration illustrationKey={career.illustration_key} />
      </span>
      <div className="plan-head__body">
        <p className="plan-head__label">Nghề chính</p>
        <p className="plan-head__career">{career.display_name}</p>
        <p className="plan-head__totals">
          Còn lại <strong>{totals.credits_remaining}</strong> tín chỉ trong{' '}
          <strong>{totals.semesters_remaining}</strong> kỳ
        </p>
      </div>
      {student.isStudent && <GenerateButton hasRoadmap onDone={onDone} />}
    </div>
  );
}

function ProposalBanner({ student }) {
  return (
    <div className="plan-banner" role="status">
      <span className="plan-banner__text">
        <AlertTriangle size={18} aria-hidden="true" />
        <strong>Lộ trình có thay đổi</strong>
      </span>
      <Button
        size="sm"
        variant="secondary"
        iconLeft={GitCompare}
        to={student.link('/m12/ke-hoach/khac-biet')}
      >
        Xem khác biệt
      </Button>
    </div>
  );
}

function InfeasibleBlock({ rows }) {
  return (
    <section className="plan-infeasible" aria-labelledby="plan-infeasible">
      <h2 id="plan-infeasible">Chưa xếp được toàn bộ</h2>
      <p>Các mục dưới đây không xếp được mà vẫn giữ đúng tiên quyết, trần và sàn tín chỉ.</p>
      <ul>
        {rows.map((row) => (
          <li key={`${row.course_id}-${row.name}`}>
            <strong>{row.name}:</strong> {row.reason}
          </li>
        ))}
      </ul>
    </section>
  );
}

function Column({ column, showOffering, selectedId, onSelect }) {
  return (
    <section className="plan-column" aria-label={column.name}>
      <header className="plan-column__head">
        <h2>{column.name}</h2>
        <Badge tone={column.credits > 0 ? 'info' : 'neutral'}>
          {column.credits}/{column.max_credits} tín chỉ
        </Badge>
      </header>
      {column.items.length === 0 ? (
        <p className="plan-column__empty">Không xếp môn nào.</p>
      ) : (
        <div className="plan-column__items">
          {column.items.map((item) => (
            <PlanItemCard
              key={item.id}
              item={item}
              showOffering={showOffering}
              selected={selectedId === item.id}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
      {column.skills.length > 0 && (
        <div className="plan-column__skills">
          <h3>Gợi ý kỹ năng, dự án</h3>
          <ul>
            {column.skills.map((skill) => (
              <li key={skill.id}>{skill.skill.name}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function OutsideBlock({ roadmap }) {
  const names = [
    ...roadmap.outside_curriculum.map((item) => item.course.name),
    ...roadmap.absent_subjects.map((subject) => subject.name),
  ];
  if (names.length === 0) {
    return null;
  }
  return (
    <div className="plan-outside">
      <Disclosure summary={`${OUTSIDE_TITLE} (${names.length})`}>
        <p>{OUTSIDE_NOTE}</p>
        <ul>
          {names.map((name) => (
            <li key={name}>{name}</li>
          ))}
        </ul>
      </Disclosure>
    </div>
  );
}

function Plan({ roadmap, student, reload }) {
  const pushes = useMediaQuery('(min-width: 1280px)');
  const [selectedId, setSelectedId] = useState(null);
  const items = roadmap.semesters.flatMap((column) => column.items);
  const selected = items.find((item) => item.id === selectedId);
  const offering = offeringSummary(items);
  return (
    <>
      <PlanHeader roadmap={roadmap} student={student} onDone={reload} />
      {offering.allDuKien && <p className="plan-notice">{NO_OFFERING_DATA}</p>}
      {roadmap.has_proposal && <ProposalBanner student={student} />}
      {roadmap.infeasible && <InfeasibleBlock rows={roadmap.unplaced} />}
      <div className={`plan-layout${selected && pushes ? ' plan-layout--with-panel' : ''}`}>
        <div className="plan-columns" role="group" aria-label="Lộ trình theo học kỳ">
          {roadmap.semesters.map((column) => (
            <Column
              key={column.id}
              column={column}
              showOffering={offering.showChip}
              selectedId={selectedId}
              onSelect={(item) => setSelectedId(item.id)}
            />
          ))}
        </div>
        {selected && (
          <PlanPanel
            key={selected.id}
            roadmap={roadmap}
            item={selected}
            canEdit={student.isStudent}
            inline={pushes}
            onClose={() => setSelectedId(null)}
            onMoved={() => {
              setSelectedId(null);
              reload();
            }}
          />
        )}
      </div>
      <OutsideBlock roadmap={roadmap} />
    </>
  );
}

function NoRoadmap({ data, student, reload }) {
  if (!data.has_primary) {
    return (
      <EmptyState
        title={student.isStudent ? 'Bạn chưa có nghề chính' : 'Sinh viên chưa có nghề chính'}
        description={
          student.isStudent
            ? 'Hãy chọn nghề chính ở trang Định hướng nghề, rồi quay lại để tạo lộ trình.'
            : 'Sinh viên cần chọn nghề chính trước khi tạo lộ trình.'
        }
        action={
          student.isStudent && (
            <Button to={student.link('/m12/dinh-huong')}>Mở Định hướng nghề</Button>
          )
        }
      />
    );
  }
  if (!student.isStudent) {
    return <EmptyState title="Sinh viên chưa tạo lộ trình" />;
  }
  return (
    <EmptyState
      title="Chưa có lộ trình"
      description="Bấm để xếp các môn còn lại vào từng học kỳ theo nghề chính của bạn."
      action={<GenerateButton hasRoadmap={false} onDone={reload} />}
    />
  );
}

export default function PlanPage() {
  const student = useCareerStudent();
  const resource = useApiResource(
    student.needsStudent ? null : withQuery(CURRENT_API, student.query),
  );
  return (
    <section className="m12-page">
      <PageHeader title="Kế hoạch học tập" />
      {student.needsStudent ? (
        <EmptyState title="Chưa chọn sinh viên" description={PICK_STUDENT_HINT} />
      ) : (
        <ResourceView
          resource={resource}
          loadingText="Đang tải lộ trình..."
          errorText="Không tải được lộ trình"
        >
          {(data) => (
            <>
              {data.roadmap ? (
                <Plan roadmap={data.roadmap} student={student} reload={resource.retry} />
              ) : (
                <NoRoadmap data={data} student={student} reload={resource.retry} />
              )}
              <p className="career-disclaimer plan-note">{data.note}</p>
            </>
          )}
        </ResourceView>
      )}
    </section>
  );
}
