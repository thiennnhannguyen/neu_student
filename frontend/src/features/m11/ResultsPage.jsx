import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';
import AttemptHistoryPanel from './AttemptHistoryPanel';
import { withQuery } from './format';
import GradesTable from './GradesTable';
import { GRADE_STATUSES } from './labels';
import M11Page from './M11Page';
import useApiResource from './useApiResource';
import { DataWarnings, ReferenceLine, ResourceView } from './ui';

const PAGE_SIZE = 20;

function pageFrom(params) {
  const page = parseInt(params.get('page') ?? '1', 10);
  return Number.isInteger(page) && page > 0 ? page : 1;
}

function ResultsContent({ scope }) {
  const [params, setParams] = useSearchParams();
  const [history, setHistory] = useState(null);
  const urlKeyword = params.get('q') ?? '';
  const [keyword, setKeyword] = useState(urlKeyword);
  const status = params.get('status') ?? '';
  const page = pageFrom(params);

  useEffect(() => setKeyword(urlKeyword), [urlKeyword]);

  function update(changes) {
    setParams((current) => {
      const next = new URLSearchParams(current);
      for (const [key, value] of Object.entries(changes)) {
        if (value) {
          next.set(key, value);
        } else {
          next.delete(key);
        }
      }
      return next;
    });
  }

  const resource = useApiResource(
    withQuery('/api/m11/grades', {
      ...scope.query,
      q: urlKeyword.trim(),
      status,
      page,
      page_size: PAGE_SIZE,
    }),
  );

  return (
    <>
      <form
        className="filter-form"
        role="search"
        onSubmit={(event) => {
          event.preventDefault();
          update({ q: keyword.trim(), page: null });
        }}
      >
        <div className="field">
          <label htmlFor="grades-q">Tìm môn</label>
          <input
            id="grades-q"
            type="search"
            value={keyword}
            placeholder="Tên hoặc mã môn"
            onChange={(event) => setKeyword(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="grades-status">Trạng thái</label>
          <select
            id="grades-status"
            value={status}
            onChange={(event) => update({ status: event.target.value, page: null })}
          >
            <option value="">Tất cả trạng thái</option>
            {Object.entries(GRADE_STATUSES).map(([value, info]) => (
              <option key={value} value={value}>
                {info.label}
              </option>
            ))}
          </select>
        </div>
        <div className="filter-form__actions">
          <button type="submit" className="button">
            Tìm
          </button>
        </div>
      </form>
      <ResourceView
        resource={resource}
        loadingText="Đang tải bảng điểm..."
        errorText="Không tải được bảng điểm"
        isEmpty={(data) => data.items.length === 0 && data.total === 0}
        emptyText="Không có môn nào phù hợp với bộ lọc."
      >
        {(data) => {
          const lastPage = Math.max(1, Math.ceil(data.total / data.page_size));
          const semesterName = scope.semesters.data.items.find(
            (item) => item.id === data.meta.reference_semester,
          )?.name;
          return (
            <>
              <GradesTable rows={data.items} onOpenHistory={setHistory} />
              <div className="pagination">
                <button
                  type="button"
                  className="button button--ghost"
                  disabled={data.page <= 1}
                  onClick={() => update({ page: String(data.page - 1) })}
                >
                  Trang trước
                </button>
                <span>
                  Trang {data.page}/{lastPage} · {data.total} môn
                </span>
                <button
                  type="button"
                  className="button button--ghost"
                  disabled={data.page >= lastPage}
                  onClick={() => update({ page: String(data.page + 1) })}
                >
                  Trang sau
                </button>
              </div>
              <ReferenceLine
                semesterName={semesterName}
                computedAt={data.meta.computed_at}
                ruleVersion={data.meta.rule_version}
              />
              <DataWarnings warnings={data.meta.data_warnings} />
            </>
          );
        }}
      </ResourceView>
      {history && (
        <AttemptHistoryPanel
          row={history}
          studentId={scope.studentId}
          onClose={() => setHistory(null)}
        />
      )}
    </>
  );
}

export default function ResultsPage() {
  return (
    <M11Page title="Kết quả" allowAll>
      {(scope) => <ResultsContent scope={scope} />}
    </M11Page>
  );
}
