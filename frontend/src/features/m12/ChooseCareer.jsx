import { useState } from 'react';
import { Link } from 'react-router';
import { Card, FormField, Pagination, SearchBox } from '../../components/ui';
import { withQuery } from '../m11/format';
import useApiResource from '../m11/useApiResource';
import { ResourceView } from '../m11/ui';
import SetGoalButton from './SetGoalButton';

const PAGE_SIZE = 12;

/** Sinh viên chưa có nghề chính: danh mục nghề đã công bố kèm tìm kiếm. */
export default function ChooseCareer({ onChanged }) {
  const [keyword, setKeyword] = useState('');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const resource = useApiResource(
    withQuery('/api/m12/careers', { q: query, page, page_size: PAGE_SIZE }),
  );

  return (
    <>
      <p className="choose-career__lead">
        Bạn chưa chọn nghề chính. Chọn một nghề để xem tiến độ; bạn có thể đổi lại bất cứ lúc nào.
      </p>
      <form
        className="filter-bar"
        role="search"
        onSubmit={(event) => {
          event.preventDefault();
          setQuery(keyword.trim());
          setPage(1);
        }}
      >
        <FormField id="choose-q" label="Tìm nghề">
          <SearchBox
            value={keyword}
            placeholder="Tên nghề"
            onChange={(event) => setKeyword(event.target.value)}
          />
        </FormField>
      </form>
      <ResourceView
        resource={resource}
        loadingText="Đang tải danh mục nghề..."
        errorText="Không tải được danh mục nghề"
        isEmpty={(data) => data.items.length === 0}
        emptyText="Không có nghề phù hợp"
      >
        {(data) => (
          <>
            <div className="career-grid">
              {data.items.map((career) => (
                <Card as="article" key={career.id} className="related-career">
                  <h2 className="related-career__name">
                    <Link to={`/m12/dinh-huong/nghe/${career.id}`}>{career.name}</Link>
                  </h2>
                  <p className="related-career__field">{career.field}</p>
                  <SetGoalButton career={career} onChanged={onChanged} label="Chọn nghề này" />
                </Card>
              ))}
            </div>
            {data.total > PAGE_SIZE && (
              <Pagination
                page={data.page}
                lastPage={Math.ceil(data.total / PAGE_SIZE)}
                summary={`Trang ${data.page}`}
                label="Phân trang danh mục nghề"
                onPage={setPage}
              />
            )}
          </>
        )}
      </ResourceView>
    </>
  );
}
