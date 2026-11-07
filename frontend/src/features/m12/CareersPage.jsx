import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router';
import { EmptyState, InfoPopover, PageHeader, SearchBox, Select } from '../../components/ui';
import { withQuery } from '../m11/format';
import useApiResource from '../m11/useApiResource';
import { ResourceView } from '../m11/ui';
import CareerCard from './CareerCard';
import { MeterLegend } from './CareerMeter';
import { groupLabel, groupShortLabel, METER_NOTE, NOT_RECRUITMENT, RATE_NOTE } from './labels';
import useCareerStudent from './useCareerStudent';

export const PICK_STUDENT_HINT =
  'Chọn sinh viên ở ô "Sinh viên" trên thanh trên cùng để xem dữ liệu. Trên điện thoại, bấm nút "Đang xem".';

const SEARCH_DELAY_MS = 250;

function GroupChips({ groups, selected, onSelect }) {
  const chips = [{ value: '', label: 'Tất cả', full: 'Tất cả' }].concat(
    groups.map((group) => ({
      value: group,
      label: groupShortLabel(group),
      full: groupLabel(group),
    })),
  );
  return (
    <div className="career-filter__chips" role="group" aria-label="Lọc theo nhóm nghề">
      {chips.map((chip) => (
        <button
          key={chip.value}
          type="button"
          className="career-filter__chip"
          title={chip.full}
          aria-label={chip.label === chip.full ? undefined : `${chip.label}: ${chip.full}`}
          aria-pressed={selected === chip.value}
          onClick={() => onSelect(chip.value)}
        >
          {chip.label}
        </button>
      ))}
    </div>
  );
}

function Gallery({ data, student, group, setFilter, busy }) {
  return (
    <>
      {!data.has_primary && student.isStudent && (
        <p className="career-remind">Chọn một nghề làm mục tiêu: mở thẻ nghề để đặt mục tiêu.</p>
      )}
      <GroupChips
        groups={data.groups}
        selected={group}
        onSelect={(value) => setFilter('group', value)}
      />
      {data.items.length === 0 ? (
        <EmptyState title="Không có nghề phù hợp" />
      ) : (
        <>
          <MeterLegend />
          <div className="career-gallery" aria-busy={busy}>
            {data.items.map((item) => (
              <CareerCard key={item.career.id} item={item} link={student.link} />
            ))}
          </div>
        </>
      )}
    </>
  );
}

export default function CareersPage() {
  const student = useCareerStudent();
  const [params, setParams] = useSearchParams();
  const group = params.get('group') ?? '';
  const keyword = params.get('q') ?? '';
  const sort = params.get('sort') ?? 'default';
  const [text, setText] = useState(keyword);
  const resource = useApiResource(
    student.needsStudent
      ? null
      : withQuery('/api/m12/gallery', {
          ...student.query,
          group: group || undefined,
          q: keyword || undefined,
          sort: sort === 'default' ? undefined : sort,
        }),
  );
  // Giữ lưới cũ khi đang lọc để trang không nhảy về khung tải.
  const last = useRef(null);
  if (resource.status === 'ok') {
    last.current = resource.data;
  }
  const shown =
    resource.status === 'loading' && last.current
      ? { status: 'ok', data: last.current, retry: resource.retry }
      : resource;

  function setFilter(name, value) {
    setParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (value) {
          next.set(name, value);
        } else {
          next.delete(name);
        }
        return next;
      },
      { replace: true },
    );
  }

  const latestSetFilter = useRef(setFilter);
  latestSetFilter.current = setFilter;
  useEffect(() => {
    const timer = window.setTimeout(
      () => latestSetFilter.current('q', text.trim()),
      SEARCH_DELAY_MS,
    );
    return () => window.clearTimeout(timer);
  }, [text]);

  return (
    <section className="m12-page">
      <PageHeader
        title="Định hướng nghề"
        actions={
          <InfoPopover label="Giải thích tỷ lệ">
            {RATE_NOTE} {METER_NOTE} {NOT_RECRUITMENT}.
          </InfoPopover>
        }
      />
      {student.needsStudent ? (
        <EmptyState title="Chưa chọn sinh viên" description={PICK_STUDENT_HINT} />
      ) : (
        <>
          <div className="career-filter">
            <SearchBox
              value={text}
              aria-label="Tìm nghề"
              placeholder="Tìm nghề"
              onChange={(event) => setText(event.target.value)}
            />
            <Select
              value={sort}
              aria-label="Sắp xếp"
              className="career-filter__sort"
              onChange={(event) =>
                setFilter('sort', event.target.value === 'default' ? '' : event.target.value)
              }
            >
              <option value="default">Mặc định</option>
              <option value="closeness">Gần nghề chính</option>
            </Select>
          </div>
          <ResourceView
            resource={shown}
            loadingText="Đang tải định hướng nghề..."
            errorText="Không tải được định hướng nghề"
          >
            {(data) => (
              <Gallery
                data={data}
                student={student}
                group={group}
                setFilter={setFilter}
                busy={resource.status === 'loading'}
              />
            )}
          </ResourceView>
        </>
      )}
    </section>
  );
}
