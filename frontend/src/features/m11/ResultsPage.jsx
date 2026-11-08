import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';
import { Button, FormField, Pagination, SearchBox, Select } from '../../components/ui';
import { STATUS_CHIPS } from '../../components/ui/StatusChip';
import { withQuery } from './format';
import GradesTable from './GradesTable';
import { GRADE_STATUS_CODES } from './labels';
import M11Page from './M11Page';
import useApiResource from './useApiResource';
import { ALL_SEMESTERS } from './useM11Scope';
import { ResourceView } from './ui';

const PAGE_SIZE = 20;
/** ?view=failed: môn chưa đạt tính đến kỳ đang xem, đúng tập mà thẻ ở Tổng quan đếm (CR-05). */
export const FAILED_VIEW = 'failed';

function pageFrom(params) {
  const page = parseInt(params.get('page') ?? '1', 10);
  return Number.isInteger(page) && page > 0 ? page : 1;
}

function ResultsContent({ scope }) {
  const [params, setParams] = useSearchParams();
  const urlKeyword = params.get('q') ?? '';
  const [keyword, setKeyword] = useState(urlKeyword);
  const failedView = params.get('view') === FAILED_VIEW;
  const allSemesters = scope.semesterId === ALL_SEMESTERS;
  const status = failedView ? '' : (params.get('status') ?? '');
  const page = pageFrom(params);

  useEffect(() => setKeyword(urlKeyword), [urlKeyword]);

  // "Tất cả các kỳ" không có mốc "tính đến": quay về bảng điểm tất cả các kỳ.
  useEffect(() => {
    if (failedView && allSemesters) {
      setParams(
        (current) => {
          const next = new URLSearchParams(current);
          next.delete('view');
          return next;
        },
        { replace: true },
      );
    }
  }, [failedView, allSemesters, setParams]);

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
    failedView && allSemesters
      ? null
      : withQuery('/api/m11/grades', {
          ...scope.query,
          q: urlKeyword.trim(),
          status,
          view: failedView ? 'failed_as_of' : null,
          page,
          page_size: PAGE_SIZE,
        }),
  );
  const semesterName = (id) => scope.semesters.data.items.find((item) => item.id === id)?.name;

  return (
    <>
      <form
        className="filter-bar"
        role="search"
        onSubmit={(event) => {
          event.preventDefault();
          update({ q: keyword.trim(), page: null });
        }}
      >
        <FormField id="grades-q" label="Tìm môn">
          <SearchBox
            value={keyword}
            placeholder="Tên hoặc mã môn"
            onChange={(event) => setKeyword(event.target.value)}
          />
        </FormField>
        {!failedView && (
          <FormField id="grades-status" label="Trạng thái">
            <Select
              value={status}
              onChange={(event) => update({ status: event.target.value, page: null })}
            >
              <option value="">Tất cả trạng thái</option>
              {GRADE_STATUS_CODES.map((code) => (
                <option key={code} value={code}>
                  {STATUS_CHIPS[code].label}
                </option>
              ))}
            </Select>
          </FormField>
        )}
        <div className="form-actions filter-bar__submit">
          <Button type="submit">Tìm</Button>
        </div>
      </form>
      <ResourceView
        resource={resource}
        loadingText="Đang tải bảng điểm..."
        errorText="Không tải được bảng điểm"
        isEmpty={(data) => !failedView && data.items.length === 0 && data.total === 0}
        emptyText="Không có môn nào phù hợp với bộ lọc."
      >
        {(data) => {
          const lastPage = Math.max(1, Math.ceil(data.total / data.page_size));
          const referenceName = semesterName(data.meta.reference_semester);
          return (
            <>
              {failedView && (
                <div className="failed-view">
                  <h2 className="failed-view__title">
                    Môn chưa đạt tính đến {referenceName}: {data.total} môn
                  </h2>
                  <Button variant="secondary" onClick={() => update({ view: null, page: null })}>
                    Xem bảng điểm kỳ này
                  </Button>
                </div>
              )}
              {failedView && data.total === 0 && (
                <p className="table-count">Không có môn chưa đạt tính đến kỳ này.</p>
              )}
              {data.total > 0 && (
                <GradesTable
                  rows={data.items}
                  studentId={scope.studentId}
                  summary={data.semester_summary}
                />
              )}
              {lastPage > 1 && (
                <Pagination
                  label="Phân trang bảng điểm"
                  page={data.page}
                  lastPage={lastPage}
                  summary={`Trang ${data.page}/${lastPage} · ${data.total} môn`}
                  onPage={(next) => update({ page: String(next) })}
                />
              )}
            </>
          );
        }}
      </ResourceView>
    </>
  );
}

export default function ResultsPage() {
  return <M11Page title="Kết quả">{(scope) => <ResultsContent scope={scope} />}</M11Page>;
}
