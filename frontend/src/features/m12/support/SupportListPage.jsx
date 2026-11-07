import { Plus } from 'lucide-react';
import { useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { Button, EmptyState, PageHeader, Pagination, Select } from '../../../components/ui';
import { useAuth } from '../../auth/AuthContext';
import { withQuery } from '../../m11/format';
import useApiResource from '../../m11/useApiResource';
import { ResourceView } from '../../m11/ui';
import SupportForm from './SupportForm';
import TicketStatus, { TICKET_STATUSES } from './TicketStatus';

const PAGE_SIZE = 20;

function TicketRow({ row, showStudent }) {
  return (
    <li>
      <Link to={`/m12/yeu-cau-ho-tro/${row.id}`} className="ticket-row">
        <span className="ticket-row__main">
          <span className="ticket-row__code">{row.code}</span>
          <strong>{row.title}</strong>
          <span className="ticket-row__meta">
            {row.category.name}
            {showStudent && ` · ${row.student.name} (${row.student.code})`}
          </span>
        </span>
        <TicketStatus status={row.status} />
      </Link>
    </li>
  );
}

export default function SupportListPage() {
  const { role } = useAuth();
  const [params, setParams] = useSearchParams();
  const [creating, setCreating] = useState(false);
  const status = params.get('status') ?? '';
  const category = params.get('category') ?? '';
  const page = parseInt(params.get('page') ?? '1', 10);
  const isStudent = role === 'student';
  const categories = useApiResource('/api/m12/support-categories');
  const resource = useApiResource(
    withQuery('/api/m12/support-requests', {
      status: status || undefined,
      category_id: category || undefined,
      page,
      page_size: PAGE_SIZE,
    }),
  );
  const items = categories.status === 'ok' ? categories.data.items : [];
  const setFilter = (key, value) => {
    const next = new URLSearchParams(params);
    next.delete('page');
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    setParams(next);
  };
  return (
    <section className="m12-page">
      <PageHeader
        title={role === 'support_staff' ? 'Hàng đợi hỗ trợ' : 'Yêu cầu hỗ trợ'}
        actions={
          isStudent && (
            <Button iconLeft={Plus} onClick={() => setCreating(true)}>
              Tạo yêu cầu
            </Button>
          )
        }
      />
      <div className="career-filter">
        <Select
          aria-label="Lọc theo trạng thái"
          className="career-filter__sort"
          value={status}
          onChange={(event) => setFilter('status', event.target.value)}
        >
          <option value="">Mọi trạng thái</option>
          {TICKET_STATUSES.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </Select>
        {!isStudent && (
          <Select
            aria-label="Lọc theo nhóm vấn đề"
            className="career-filter__sort"
            value={category}
            onChange={(event) => setFilter('category', event.target.value)}
          >
            <option value="">Mọi nhóm</option>
            {items.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </Select>
        )}
      </div>
      <ResourceView
        resource={resource}
        loadingText="Đang tải yêu cầu..."
        errorText="Không tải được yêu cầu"
      >
        {(data) =>
          data.items.length === 0 ? (
            <EmptyState title="Chưa có yêu cầu nào" />
          ) : (
            <>
              <ul className="ticket-list">
                {data.items.map((row) => (
                  <TicketRow key={row.id} row={row} showStudent={!isStudent} />
                ))}
              </ul>
              <Pagination
                page={data.page}
                lastPage={Math.max(1, Math.ceil(data.total / data.page_size))}
                summary={`${data.total} yêu cầu`}
                label="Phân trang yêu cầu"
                onPage={(next) => setFilter('page', String(next))}
              />
            </>
          )
        }
      </ResourceView>
      {creating && <SupportForm categories={items} onClose={() => setCreating(false)} />}
    </section>
  );
}
