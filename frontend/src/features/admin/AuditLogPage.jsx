import { useCallback, useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';

const PAGE_SIZE = 20;
const EMPTY_FILTERS = { entity: '', actor: '', from: '', to: '' };

/** Ô ngày theo giờ địa phương, đổi sang mốc UTC cho đúng ngày người dùng chọn. */
function dayBound(value, time) {
  return new Date(`${value}T${time}`).toISOString();
}

function buildQuery(filters, page) {
  const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
  if (filters.entity.trim()) {
    params.set('entity', filters.entity.trim());
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

function formatJson(value) {
  return value === null ? '—' : JSON.stringify(value);
}

function FilterField({ id, label, type = 'text', value, errors, onChange }) {
  const errorId = `${id}-error`;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        aria-invalid={errors ? 'true' : undefined}
        aria-describedby={errors ? errorId : undefined}
      />
      {errors && (
        <p id={errorId} className="status-error field__error">
          {errors.join(' ')}
        </p>
      )}
    </div>
  );
}

export default function AuditLogPage() {
  const [draft, setDraft] = useState(EMPTY_FILTERS);
  const [applied, setApplied] = useState({ filters: EMPTY_FILTERS, page: 1, attempt: 0 });
  const [state, setState] = useState({ status: 'loading' });
  const [fieldErrors, setFieldErrors] = useState({});

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
    <section className="card">
      <h1>Nhật ký thay đổi</h1>
      <form className="filter-form" onSubmit={handleFilter} noValidate>
        <FilterField
          id="audit-entity"
          label="Đối tượng"
          value={draft.entity}
          errors={fieldErrors.entity}
          onChange={updateDraft('entity')}
        />
        <FilterField
          id="audit-actor"
          label="Tên đăng nhập người thực hiện"
          value={draft.actor}
          errors={fieldErrors.actor}
          onChange={updateDraft('actor')}
        />
        <FilterField
          id="audit-from"
          label="Từ ngày"
          type="date"
          value={draft.from}
          errors={fieldErrors.from}
          onChange={updateDraft('from')}
        />
        <FilterField
          id="audit-to"
          label="Đến ngày"
          type="date"
          value={draft.to}
          errors={fieldErrors.to}
          onChange={updateDraft('to')}
        />
        <div className="filter-form__actions">
          <button type="submit" className="button">
            Lọc
          </button>
          <button type="button" className="button button--ghost" onClick={clearFilters}>
            Xóa lọc
          </button>
        </div>
      </form>
      <AuditLogResult state={state} onRetry={retry} onPage={goToPage} />
    </section>
  );
}

function AuditLogResult({ state, onRetry, onPage }) {
  if (state.status === 'loading') {
    return <p role="status">Đang tải nhật ký...</p>;
  }
  if (state.status === 'error') {
    return (
      <div role="alert">
        <p className="status-error">Không tải được nhật ký: {state.message}</p>
        <button type="button" className="button" onClick={onRetry}>
          Thử lại
        </button>
      </div>
    );
  }

  const { items, page, page_size: pageSize, total } = state.result;
  if (total === 0) {
    return <p role="status">Không có bản ghi nhật ký phù hợp.</p>;
  }
  const lastPage = Math.max(1, Math.ceil(total / pageSize));

  return (
    <>
      {/* Bảng tự cuộn ngang trong khung này để trang không tràn ở màn hình 375px. */}
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- cuộn được bằng bàn phím */}
      <div className="table-scroll" role="region" aria-label="Bảng nhật ký" tabIndex={0}>
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Thời gian</th>
              <th scope="col">Người thực hiện</th>
              <th scope="col">Hành động</th>
              <th scope="col">Đối tượng</th>
              <th scope="col">Mã đối tượng</th>
              <th scope="col">Trước</th>
              <th scope="col">Sau</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{new Date(item.created_at).toLocaleString('vi-VN')}</td>
                <td>{item.actor_username ?? 'Hệ thống'}</td>
                <td>{item.action}</td>
                <td>{item.entity}</td>
                <td>{item.entity_id}</td>
                <td className="data-table__json">{formatJson(item.before)}</td>
                <td className="data-table__json">{formatJson(item.after)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <nav className="pagination" aria-label="Phân trang nhật ký">
        <button
          type="button"
          className="button button--ghost"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
        >
          Trang trước
        </button>
        <span>
          Trang {page} / {lastPage} ({total} bản ghi)
        </span>
        <button
          type="button"
          className="button button--ghost"
          disabled={page >= lastPage}
          onClick={() => onPage(page + 1)}
        >
          Trang sau
        </button>
      </nav>
    </>
  );
}
