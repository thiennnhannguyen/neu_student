import { Eye, FilterX, ListFilter } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import useApiResource from '../m11/useApiResource';
import {
  Button,
  Card,
  DataTable,
  EmptyState,
  ErrorState,
  FormField,
  Input,
  PageHeader,
  Pagination,
  SearchBox,
  Select,
  SidePanel,
  Skeleton,
} from '../../components/ui';

const PAGE_SIZE = 20;
const EMPTY_FILTERS = { entity: '', actor: '', from: '', to: '' };
const NO_VALUE = '—';
/** Danh sách lấy từ API; loại chưa có tên ở đây thì hiện mã gốc. */
const ENTITY_NAMES = {
  career: 'Nghề',
  career_goal: 'Mục tiêu nghề',
  career_node: 'Nhóm năng lực',
  career_requirement: 'Yêu cầu của nghề',
  career_version: 'Phiên bản nghề',
  course_skill_mapping: 'Ánh xạ môn và kỹ năng',
  grade_attempt: 'Kết quả học phần',
  roadmap_version: 'Phiên bản lộ trình',
  skill: 'Kỹ năng',
  skill_evidence: 'Minh chứng',
  student: 'Sinh viên',
  support_request: 'Yêu cầu hỗ trợ',
  user: 'Tài khoản',
};

function entityLabel(entity) {
  return ENTITY_NAMES[entity] ? `${ENTITY_NAMES[entity]} (${entity})` : entity;
}

/** Ô ngày theo giờ địa phương, đổi sang mốc UTC cho đúng ngày người dùng chọn. */
function dayBound(value, time) {
  return new Date(`${value}T${time}`).toISOString();
}

function buildQuery(filters, page) {
  const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
  if (filters.entity) {
    params.set('entity', filters.entity);
  }
  if (filters.actor.trim()) {
    params.set('actor', filters.actor.trim());
  }
  if (filters.from) {
    params.set('from', dayBound(filters.from, '00:00:00.000'));
  }
  if (filters.to) {
    params.set('to', dayBound(filters.to, '23:59:59.999'));
  }
  return params.toString();
}

function formatValue(value) {
  if (value === null || value === undefined) {
    return NO_VALUE;
  }
  return typeof value === 'object' ? JSON.stringify(value) : String(value);
}

/** So sánh 2 cột theo từng trường, không đổ JSON thô. */
function AuditDetail({ item, onClose }) {
  const before = item.before ?? {};
  const after = item.after ?? {};
  const fields = [...new Set([...Object.keys(before), ...Object.keys(after)])].sort();
  return (
    <SidePanel title={`Bản ghi #${item.id}: ${item.action}`} wide onClose={onClose}>
      <dl className="detail-list">
        <div>
          <dt>Thời gian</dt>
          <dd>{new Date(item.created_at).toLocaleString('vi-VN')}</dd>
        </div>
        <div>
          <dt>Người thực hiện</dt>
          <dd>{item.actor_username ?? 'Hệ thống'}</dd>
        </div>
        <div>
          <dt>Đối tượng</dt>
          <dd>
            {item.entity} · {item.entity_id}
          </dd>
        </div>
      </dl>
      {fields.length === 0 ? (
        <p className="empty-state">Bản ghi này không có dữ liệu trước và sau.</p>
      ) : (
        <table className="diff-table">
          <caption className="visually-hidden">So sánh trước và sau</caption>
          <thead>
            <tr>
              <th scope="col">Trường</th>
              <th scope="col">Trước</th>
              <th scope="col">Sau</th>
            </tr>
          </thead>
          <tbody>
            {fields.map((field) => {
              const first = formatValue(before[field]);
              const second = formatValue(after[field]);
              return (
                <tr key={field}>
                  <th scope="row">{field}</th>
                  <td>{first}</td>
                  <td className={first === second ? undefined : 'diff-table__changed'}>{second}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </SidePanel>
  );
}

export default function AuditLogPage() {
  const [draft, setDraft] = useState(EMPTY_FILTERS);
  const [applied, setApplied] = useState({ filters: EMPTY_FILTERS, page: 1, attempt: 0 });
  const [state, setState] = useState({ status: 'loading' });
  const [fieldErrors, setFieldErrors] = useState({});
  const entities = useApiResource('/api/admin/audit-logs/entities');
  const entityItems = entities.status === 'ok' ? entities.data.items : [];

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: 'loading' });
    apiRequest(`/api/admin/audit-logs?${buildQuery(applied.filters, applied.page)}`, {
      signal: controller.signal,
    })
      .then((result) => {
        setFieldErrors({});
        setState({ status: 'ok', result });
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setFieldErrors(error.details?.fields ?? {});
          setState({ status: 'error', message: error.message });
        }
      });
    return () => controller.abort();
  }, [applied]);

  const goToPage = useCallback((page) => {
    setApplied((current) => ({ ...current, page }));
  }, []);

  function updateDraft(name) {
    return (event) => setDraft((current) => ({ ...current, [name]: event.target.value }));
  }

  function handleFilter(event) {
    event.preventDefault();
    setApplied((current) => ({ filters: draft, page: 1, attempt: current.attempt + 1 }));
  }

  function clearFilters() {
    setDraft(EMPTY_FILTERS);
    setApplied((current) => ({ filters: EMPTY_FILTERS, page: 1, attempt: current.attempt + 1 }));
  }

  function retry() {
    setApplied((current) => ({ ...current, attempt: current.attempt + 1 }));
  }

  return (
    <>
      <PageHeader
        title="Nhật ký thay đổi"
        description="Ai đã đổi gì, khi nào. Bấm Xem để so sánh trước và sau."
      />
      <Card>
        <form className="filter-bar" onSubmit={handleFilter} noValidate>
          <FormField
            id="audit-actor"
            label="Tên đăng nhập người thực hiện"
            errors={fieldErrors.actor}
          >
            <SearchBox value={draft.actor} onChange={updateDraft('actor')} />
          </FormField>
          <FormField
            id="audit-entity"
            label="Đối tượng"
            errors={fieldErrors.entity}
            hint={entities.status === 'error' ? 'Không tải được danh sách đối tượng.' : undefined}
          >
            <Select value={draft.entity} onChange={updateDraft('entity')}>
              <option value="">Tất cả đối tượng</option>
              {entityItems.map((entity) => (
                <option key={entity} value={entity}>
                  {entityLabel(entity)}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField id="audit-from" label="Từ ngày" errors={fieldErrors.from}>
            <Input type="date" value={draft.from} onChange={updateDraft('from')} />
          </FormField>
          <FormField id="audit-to" label="Đến ngày" errors={fieldErrors.to}>
            <Input type="date" value={draft.to} onChange={updateDraft('to')} />
          </FormField>
          <div className="form-actions filter-bar__actions">
            <Button type="submit" iconLeft={ListFilter}>
              Lọc
            </Button>
            <Button variant="ghost" iconLeft={FilterX} onClick={clearFilters}>
              Xóa lọc
            </Button>
          </div>
        </form>
      </Card>
      <AuditLogResult state={state} onRetry={retry} onPage={goToPage} />
    </>
  );
}

function AuditLogResult({ state, onRetry, onPage }) {
  const [detail, setDetail] = useState(null);

  if (state.status === 'loading') {
    return (
      <div className="result-block">
        <p role="status" className="visually-hidden">
          Đang tải nhật ký...
        </p>
        <Skeleton height={44} />
        <Skeleton height={44} />
        <Skeleton height={44} />
      </div>
    );
  }
  if (state.status === 'error') {
    return (
      <div className="result-block">
        <ErrorState title="Không tải được nhật ký" description={state.message} onRetry={onRetry} />
      </div>
    );
  }

  const { items, page, page_size: pageSize, total } = state.result;
  if (total === 0) {
    return (
      <div className="result-block">
        <EmptyState
          title="Không có bản ghi nhật ký phù hợp."
          description="Thử bỏ bớt bộ lọc hoặc mở rộng khoảng ngày."
        />
      </div>
    );
  }
  const lastPage = Math.max(1, Math.ceil(total / pageSize));
  const columns = [
    {
      key: 'created_at',
      header: 'Thời gian',
      sortable: true,
      render: (item) => new Date(item.created_at).toLocaleString('vi-VN'),
    },
    {
      key: 'actor',
      header: 'Người thực hiện',
      sortable: true,
      sortValue: (item) => item.actor_username,
      render: (item) => item.actor_username ?? 'Hệ thống',
    },
    { key: 'action', header: 'Hành động', sortable: true },
    { key: 'entity', header: 'Đối tượng', sortable: true },
    { key: 'entity_id', header: 'Mã đối tượng' },
    {
      key: 'detail',
      header: 'Chi tiết',
      render: (item) => (
        <Button
          variant="ghost"
          size="sm"
          iconLeft={Eye}
          aria-label={`Xem chi tiết bản ghi ${item.id}`}
          onClick={() => setDetail(item)}
        >
          Xem
        </Button>
      ),
    },
  ];

  return (
    <div className="result-block">
      <DataTable
        columns={columns}
        rows={items}
        rowKey={(item) => item.id}
        ariaLabel="Bảng nhật ký"
      />
      <Pagination
        label="Phân trang nhật ký"
        page={page}
        lastPage={lastPage}
        summary={`Trang ${page} / ${lastPage} (${total} bản ghi)`}
        onPage={onPage}
      />
      {detail && <AuditDetail item={detail} onClose={() => setDetail(null)} />}
    </div>
  );
}
