import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';
import {
  Button,
  EmptyState,
  FormField,
  PageHeader,
  Pagination,
  SearchBox,
  Select,
} from '../../components/ui';
import { withQuery } from '../m11/format';
import useApiResource from '../m11/useApiResource';
import { DataWarnings, ResourceView } from '../m11/ui';
import { PICK_STUDENT_HINT } from './CareersPage';
import RelatedCareerCard from './RelatedCareerCard';
import useCareerStudent from './useCareerStudent';

const PAGE_SIZE = 12;
const SORTS = [
  { value: 'closeness', label: 'Gần nghề chính' },
  { value: 'profile_fit', label: 'Phù hợp hồ sơ' },
];
const LEVELS = [
  { value: '', label: 'Mọi mức tiến độ' },
  { value: '25', label: 'Từ 25% học phần' },
  { value: '50', label: 'Từ 50% học phần' },
  { value: '75', label: 'Từ 75% học phần' },
];

function pageFrom(params) {
  const page = parseInt(params.get('page') ?? '1', 10);
  return Number.isInteger(page) && page > 0 ? page : 1;
}

function Results({ student, resource, page, onPage }) {
  return (
    <ResourceView
      resource={resource}
      loadingText="Đang tải danh sách nghề..."
      errorText="Không tải được danh sách nghề"
    >
      {(data) => (
        <>
          <DataWarnings warnings={data.data_warnings} />
          {data.items.length === 0 ? (
            <EmptyState compact title="Không có nghề phù hợp với bộ lọc" />
          ) : (
            <div className="career-grid">
              {data.items.map((item) => (
                <RelatedCareerCard
                  key={item.career.id}
                  item={item}
                  link={student.link}
                  disclaimer={data.disclaimer}
                />
              ))}
            </div>
          )}
          {data.total > PAGE_SIZE && (
            <Pagination
              page={page}
              lastPage={Math.ceil(data.total / PAGE_SIZE)}
              summary={`Trang ${page}, ${data.total} nghề`}
              label="Phân trang danh sách nghề"
              onPage={onPage}
            />
          )}
          <p className="career-disclaimer">{data.disclaimer}.</p>
        </>
      )}
    </ResourceView>
  );
}

/** Giữ danh sách lĩnh vực lần đầu có, để ô lọc không mất lựa chọn khi đang lọc. */
function useFields(resource) {
  const [fields, setFields] = useState([]);
  const loaded = resource.status === 'ok' ? resource.data.fields : null;
  useEffect(() => {
    if (loaded) {
      setFields(loaded);
    }
  }, [loaded]);
  return fields;
}

export default function AllCareersPage() {
  const student = useCareerStudent();
  const [params, setParams] = useSearchParams();
  const urlKeyword = params.get('q') ?? '';
  const [keyword, setKeyword] = useState(urlKeyword);
  const sort = params.get('sort') ?? 'closeness';
  const field = params.get('field') ?? '';
  const level = params.get('min_progress') ?? '';
  const page = pageFrom(params);

  useEffect(() => setKeyword(urlKeyword), [urlKeyword]);

  const resource = useApiResource(
    student.needsStudent
      ? null
      : withQuery('/api/m12/related', {
          ...student.query,
          sort,
          field,
          q: urlKeyword.trim(),
          min_progress: level,
          page,
          page_size: PAGE_SIZE,
        }),
  );
  const fields = useFields(resource);

  function update(changes) {
    setParams((current) => {
      const next = new URLSearchParams(current);
      next.delete('page');
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

  return (
    <section className="m12-page">
      <PageHeader
        title="Tất cả nghề"
        description="Hai cách xếp tách riêng, không gộp thành một điểm."
      />
      {student.needsStudent ? (
        <EmptyState title="Chưa chọn sinh viên" description={PICK_STUDENT_HINT} />
      ) : (
        <>
          <form
            className="filter-bar"
            role="search"
            onSubmit={(event) => {
              event.preventDefault();
              update({ q: keyword.trim() });
            }}
          >
            <FormField id="careers-q" label="Tìm nghề">
              <SearchBox
                value={keyword}
                placeholder="Tên nghề"
                onChange={(event) => setKeyword(event.target.value)}
              />
            </FormField>
            <FormField id="careers-field" label="Lĩnh vực">
              <Select value={field} onChange={(event) => update({ field: event.target.value })}>
                <option value="">Mọi lĩnh vực</option>
                {fields.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField id="careers-sort" label="Sắp xếp">
              <Select value={sort} onChange={(event) => update({ sort: event.target.value })}>
                {SORTS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField id="careers-level" label="Mức tiến độ">
              <Select
                value={level}
                onChange={(event) => update({ min_progress: event.target.value })}
              >
                {LEVELS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </FormField>
            <div className="filter-bar__actions">
              <Button type="submit" variant="secondary">
                Tìm
              </Button>
            </div>
          </form>
          <Results
            student={student}
            resource={resource}
            page={page}
            onPage={(value) =>
              setParams((current) => {
                const next = new URLSearchParams(current);
                next.set('page', String(value));
                return next;
              })
            }
          />
        </>
      )}
    </section>
  );
}
