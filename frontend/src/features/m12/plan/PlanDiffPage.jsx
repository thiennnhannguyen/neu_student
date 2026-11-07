import { ArrowRight, Minus, Plus } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router';
import { apiRequest } from '../../../api/client';
import { Button, EmptyState, PageHeader, useToast } from '../../../components/ui';
import { withQuery } from '../../m11/format';
import useApiResource from '../../m11/useApiResource';
import { ResourceView } from '../../m11/ui';
import { PICK_STUDENT_HINT } from '../CareersPage';
import { NO_CODE } from '../labels';
import useCareerStudent from '../useCareerStudent';
import { CURRENT_API } from './labels';

const PLAN_PATH = '/m12/ke-hoach';

function Row({ tone, icon: Icon, label, row, semester }) {
  return (
    <li className={`plan-diff__row plan-diff__row--${tone}`}>
      <span className="plan-diff__tag">
        <Icon size={14} aria-hidden="true" />
        {label}
      </span>
      <span className="plan-diff__name">
        {row.name}
        {row.kind === 'course' && <span className="plan-diff__code"> ({row.code ?? NO_CODE})</span>}
      </span>
      <span className="plan-diff__semester">{semester ?? 'Không xếp kỳ'}</span>
    </li>
  );
}

function Compare({ proposal }) {
  return (
    <div className="plan-diff">
      <section aria-labelledby="plan-diff-before" className="plan-diff__column">
        <h2 id="plan-diff-before">Bản hiện tại</h2>
        <ul>
          {proposal.removed.map((row) => (
            <Row
              key={row.id}
              tone="removed"
              icon={Minus}
              label="Bớt"
              row={row}
              semester={row.semester}
            />
          ))}
          {proposal.moved.map((row) => (
            <Row
              key={row.id}
              tone="moved"
              icon={ArrowRight}
              label="Chuyển kỳ"
              row={row}
              semester={row.from_semester}
            />
          ))}
        </ul>
      </section>
      <section aria-labelledby="plan-diff-after" className="plan-diff__column">
        <h2 id="plan-diff-after">Bản đề xuất</h2>
        <ul>
          {proposal.added.map((row) => (
            <Row
              key={row.id}
              tone="added"
              icon={Plus}
              label="Thêm"
              row={row}
              semester={row.semester}
            />
          ))}
          {proposal.moved.map((row) => (
            <Row
              key={row.id}
              tone="moved"
              icon={ArrowRight}
              label="Chuyển kỳ"
              row={row}
              semester={row.to_semester}
            />
          ))}
        </ul>
      </section>
    </div>
  );
}

function Actions({ proposal, student }) {
  const { show } = useToast();
  const navigate = useNavigate();
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  async function run(action, message) {
    setBusy(action);
    setError('');
    try {
      await apiRequest(`/api/m12/roadmaps/${proposal.roadmap_id}/proposal/${action}`, {
        method: 'POST',
        body: { stamp: proposal.stamp },
      });
      show(message);
      navigate(student.link(PLAN_PATH));
    } catch (cause) {
      setError(cause.message);
      setBusy('');
    }
  }

  return (
    <div className="plan-diff__actions">
      <Button loading={busy === 'accept'} onClick={() => run('accept', 'Đã áp dụng lộ trình mới.')}>
        Áp dụng
      </Button>
      <Button
        variant="secondary"
        loading={busy === 'dismiss'}
        onClick={() => run('dismiss', 'Đã giữ bản cũ.')}
      >
        Giữ bản cũ
      </Button>
      {error && (
        <p role="alert" className="status-error">
          {error}
        </p>
      )}
    </div>
  );
}

function Proposal({ roadmapId, student }) {
  const resource = useApiResource(`/api/m12/roadmaps/${roadmapId}/proposal`);
  return (
    <ResourceView
      resource={resource}
      loadingText="Đang so sánh..."
      errorText="Không tải được khác biệt"
    >
      {(proposal) =>
        proposal.has_proposal ? (
          <>
            {proposal.career_before.id !== proposal.career_after.id && (
              <p className="plan-diff__career">
                Nghề chính đổi từ <strong>{proposal.career_before.display_name}</strong> sang{' '}
                <strong>{proposal.career_after.display_name}</strong>.
              </p>
            )}
            <p className="plan-diff__count">
              Thêm {proposal.added.length} · Bớt {proposal.removed.length} · Chuyển kỳ{' '}
              {proposal.moved.length}
            </p>
            {proposal.infeasible && (
              <div role="status" className="plan-infeasible">
                <strong>Bản đề xuất chưa xếp được:</strong>
                <ul>
                  {proposal.unplaced.map((row) => (
                    <li key={`${row.course_id}-${row.name}`}>
                      {row.name}: {row.reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <Compare proposal={proposal} />
            {student.isStudent && <Actions proposal={proposal} student={student} />}
            <p className="career-disclaimer plan-note">{proposal.note}</p>
          </>
        ) : (
          <EmptyState
            title="Không có thay đổi"
            description="Lộ trình hiện tại vẫn đúng với dữ liệu mới nhất."
          />
        )
      }
    </ResourceView>
  );
}

export default function PlanDiffPage() {
  const student = useCareerStudent();
  const resource = useApiResource(
    student.needsStudent ? null : withQuery(CURRENT_API, student.query),
  );
  return (
    <section className="m12-page">
      <PageHeader title="Khác biệt của lộ trình" />
      <p>
        <Button variant="ghost" size="sm" to={student.link(PLAN_PATH)}>
          Về Kế hoạch học tập
        </Button>
      </p>
      {student.needsStudent ? (
        <EmptyState title="Chưa chọn sinh viên" description={PICK_STUDENT_HINT} />
      ) : (
        <ResourceView
          resource={resource}
          loadingText="Đang tải..."
          errorText="Không tải được lộ trình"
        >
          {(data) =>
            data.roadmap ? (
              <Proposal roadmapId={data.roadmap.id} student={student} />
            ) : (
              <EmptyState title="Chưa có lộ trình" />
            )
          }
        </ResourceView>
      )}
    </section>
  );
}
