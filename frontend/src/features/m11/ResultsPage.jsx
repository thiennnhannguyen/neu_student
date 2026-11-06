import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';
import { Button, FormField, Pagination, SearchBox, Select } from '../../components/ui';
import { STATUS_CHIPS } from '../../components/ui/StatusChip';
import AttemptHistoryPanel from './AttemptHistoryPanel';
import { withQuery } from './format';
import GradesTable from './GradesTable';
import { GRADE_STATUS_CODES } from './labels';
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
        <div className="form-actions filter-bar__submit">
          <Button type="submit">Tìm</Button>
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
              <Pagination
                label="Phân trang bảng điểm"
                page={data.page}
                lastPage={lastPage}
                summary={`Trang ${data.page}/${lastPage} · ${data.total} môn`}
                onPage={(next) => update({ page: String(next) })}
              />
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
    <M11Page
      title="Kết quả"
      description="Bảng điểm theo học kỳ, gồm cả môn chưa học khi xem tất cả các kỳ."
    >
      {(scope) => <ResultsContent scope={scope} />}
    </M11Page>
  );
}
