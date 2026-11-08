import { Plus, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { apiRequest } from '../../api/client';
import { Button, EmptyState, Input, PageHeader, useToast } from '../../components/ui';
import useCareerStudent from '../m12/useCareerStudent';
import { PICK_STUDENT_HINT } from '../m12/CareersPage';
import { withQuery } from './format';
import useApiResource from './useApiResource';
import { ResourceView } from './ui';

const URL = '/api/m12/improvement-plan';

function useAction(reload) {
  const [error, setError] = useState('');
  const run = async (path, options) => {
    setError('');
    try {
      await apiRequest(path, options);
      reload();
      return true;
    } catch (cause) {
      setError(cause.message);
      return false;
    }
  };
  return { error, run };
}

function PlanItem({ planId, item, canEdit, run }) {
  const url = `${URL}/${planId}/items/${item.id}`;
  const [title, setTitle] = useState(item.title);
  if (!canEdit) {
    return (
      <li className={`plan-item${item.done ? ' plan-item--done' : ''}`}>
        <span className="plan-item__title">{item.title}</span>
        <span>{item.done ? 'Đã xong' : 'Chưa xong'}</span>
        <span>{item.due_date ? `Hạn ${item.due_date}` : 'Chưa đặt hạn'}</span>
      </li>
    );
  }
  return (
    <li className={`plan-item${item.done ? ' plan-item--done' : ''}`}>
      <input
        type="checkbox"
        aria-label={`Đánh dấu xong: ${item.title}`}
        checked={item.done}
        onChange={(event) => run(url, { method: 'PATCH', body: { done: event.target.checked } })}
      />
      <Input
        className="plan-item__title"
        aria-label={`Nội dung: ${item.title}`}
        value={title}
        maxLength={255}
        onChange={(event) => setTitle(event.target.value)}
        onBlur={() => {
          if (title.trim() && title !== item.title) {
            run(url, { method: 'PATCH', body: { title } });
          }
        }}
      />
      <Input
        className="plan-item__date"
        type="date"
        aria-label={`Hạn: ${item.title}`}
        value={item.due_date ?? ''}
        onChange={(event) =>
          run(url, { method: 'PATCH', body: { due_date: event.target.value || null } })
        }
      />
      <Button
        variant="ghost"
        size="sm"
        iconLeft={Trash2}
        aria-label={`Xóa: ${item.title}`}
        onClick={() => run(url, { method: 'DELETE' })}
      />
    </li>
  );
}

function AddItem({ planId, run }) {
  const [title, setTitle] = useState('');
  return (
    <form
      className="plan-item-add"
      onSubmit={async (event) => {
        event.preventDefault();
        if (await run(`${URL}/${planId}/items`, { method: 'POST', body: { title } })) {
          setTitle('');
        }
      }}
    >
      <Input
        aria-label="Mục mới"
        placeholder="Thêm mục mới"
        required
        maxLength={255}
        value={title}
        onChange={(event) => setTitle(event.target.value)}
      />
      <Button type="submit" variant="secondary" iconLeft={Plus}>
        Thêm
      </Button>
    </form>
  );
}

function Plan({ data, canEdit, reload }) {
  const { error, run } = useAction(reload);
  const { plan } = data;
  return (
    <>
      {canEdit && data.new_rules.length > 0 && (
        <div className="plan-banner" role="status">
          <strong>Có rủi ro mới chưa nằm trong kế hoạch</strong>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => run(`${URL}/${plan.id}/new-risks`, { method: 'POST', body: {} })}
          >
            Thêm mục cho rủi ro mới
          </Button>
        </div>
      )}
      <ul className="plan-items">
        {plan.items.map((item) => (
          <PlanItem key={item.id} planId={plan.id} item={item} canEdit={canEdit} run={run} />
        ))}
      </ul>
      {canEdit && <AddItem planId={plan.id} run={run} />}
      {error && (
        <p role="alert" className="status-error">
          {error}
        </p>
      )}
    </>
  );
}

function NoPlan({ data, canEdit, reload }) {
  const { show } = useToast();
  const { error, run } = useAction(reload);
  if (data.active_rules.length === 0) {
    return <EmptyState title="Không có quy tắc nào ở mức chú ý hoặc cảnh báo" />;
  }
  if (!canEdit) {
    return <EmptyState title="Sinh viên chưa tạo kế hoạch cải thiện" />;
  }
  return (
    <EmptyState
      title="Chưa có kế hoạch cải thiện"
      description={`Sinh checklist từ ${data.active_rules.length} quy tắc đang cần chú ý.`}
      action={
        <>
          <Button
            onClick={async () => {
              if (await run(URL, { method: 'POST', body: {} })) {
                show('Đã tạo kế hoạch cải thiện.');
              }
            }}
          >
            Tạo kế hoạch cải thiện
          </Button>
          {error && (
            <p role="alert" className="status-error">
              {error}
            </p>
          )}
        </>
      }
    />
  );
}

export default function ImprovementPlanPage() {
  const student = useCareerStudent();
  const resource = useApiResource(student.needsStudent ? null : withQuery(URL, student.query));
  return (
    <section className="m12-page">
      <PageHeader title="Kế hoạch cải thiện" />
      <p>
        <Button variant="ghost" size="sm" to={student.link('/m11/phan-tich')}>
          Về Phân tích & Cảnh báo
        </Button>
      </p>
      {student.needsStudent ? (
        <EmptyState title="Chưa chọn sinh viên" description={PICK_STUDENT_HINT} />
      ) : (
        <ResourceView
          resource={resource}
          loadingText="Đang tải kế hoạch..."
          errorText="Không tải được kế hoạch"
        >
          {(data) => (
            <>
              {data.plan ? (
                <Plan data={data} canEdit={student.isStudent} reload={resource.retry} />
              ) : (
                <NoPlan data={data} canEdit={student.isStudent} reload={resource.retry} />
              )}
              <p className="career-disclaimer plan-note">{data.disclaimer}.</p>
            </>
          )}
        </ResourceView>
      )}
    </section>
  );
}
