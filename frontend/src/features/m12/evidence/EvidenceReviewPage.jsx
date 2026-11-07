import { useState } from 'react';
import { useSearchParams } from 'react-router';
import { apiRequest } from '../../../api/client';
import {
  Button,
  DataTable,
  EmptyState,
  FormField,
  PageHeader,
  Pagination,
  Select,
  SidePanel,
  useToast,
} from '../../../components/ui';
import { useAuth } from '../../auth/AuthContext';
import { formatDateTime, withQuery } from '../../m11/format';
import useApiResource from '../../m11/useApiResource';
import { ResourceView } from '../../m11/ui';
import AttachmentList from '../AttachmentList';

const PAGE_SIZE = 20;
const STATUSES = [
  { value: 'pending', label: 'Chờ duyệt' },
  { value: 'approved', label: 'Đã duyệt' },
  { value: 'rejected', label: 'Bị từ chối' },
  { value: '', label: 'Tất cả' },
];

function statusLabel(status) {
  return STATUSES.find((item) => item.value === status).label;
}

function submittedText(row) {
  return row.submitted_at ? formatDateTime(row.submitted_at) : 'Chưa ghi nhận';
}

function CareerGroups({ careers }) {
  if (careers.length === 0) {
    return 'Không thuộc nghề nào';
  }
  return (
    <ul className="evidence-careers">
      {careers.map((item) => (
        <li key={`${item.id}-${item.group}`}>
          {item.name}: {item.group}
        </li>
      ))}
    </ul>
  );
}

function fieldError(cause) {
  return cause.details?.fields?.note?.[0] ?? cause.message;
}

function ReviewActions({ row, onDone }) {
  const { show } = useToast();
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  async function run(action, message) {
    setBusy(action);
    setError('');
    try {
      await apiRequest(`/api/m12/evidence-reviews/${row.id}/${action}`, {
        method: 'POST',
        body: note.trim() ? { note } : {},
      });
      show(message);
      onDone();
    } catch (cause) {
      setError(fieldError(cause));
      setBusy('');
    }
  }

  return (
    <div className="evidence-review">
      <FormField
        id="evidence-note"
        label="Lý do, nhận xét"
        hint="Bắt buộc khi từ chối. Sinh viên sẽ thấy nội dung này."
      >
        <textarea
          id="evidence-note"
          className="ui-input ui-textarea"
          rows={3}
          value={note}
          onChange={(event) => setNote(event.target.value)}
        />
      </FormField>
      {error && (
        <p role="alert" className="status-error">
          {error}
        </p>
      )}
      <div className="evidence-review__buttons">
        <Button loading={busy === 'approve'} onClick={() => run('approve', 'Đã duyệt minh chứng.')}>
          Duyệt
        </Button>
        <Button
          variant="danger"
          loading={busy === 'reject'}
          onClick={() => run('reject', 'Đã từ chối minh chứng.')}
        >
          Từ chối
        </Button>
      </div>
    </div>
  );
}

function ReviewPanel({ row, canReview, onClose, onDone }) {
  return (
    <SidePanel title={row.skill.name} onClose={onClose}>
      <p>
        <strong>Sinh viên: </strong>
        {row.student.name} ({row.student.code})
      </p>
      <p>
        <strong>Trạng thái: </strong>
        {statusLabel(row.status)}
      </p>
      <p>
        <strong>Ngày nộp: </strong>
        {submittedText(row)}
      </p>
      <p>
        <strong>Số lần nộp trước: </strong>
        {row.previous_submissions}
      </p>
      <h3>Nghề, nhóm năng lực</h3>
      <CareerGroups careers={row.careers} />
      <h3>Mô tả</h3>
      <p>{row.description}</p>
      {row.link && (
        <p>
          <a href={row.link} target="_blank" rel="noreferrer">
            {row.link}
          </a>
        </p>
      )}
      <h3>Tệp đính kèm</h3>
      {row.attachments.length === 0 ? (
        <p>Không có tệp đính kèm.</p>
      ) : (
        <AttachmentList items={row.attachments} />
      )}
      {row.review_note && (
        <p>
          <strong>Nhận xét: </strong>
          {row.review_note}
        </p>
      )}
      {canReview && row.status === 'pending' && <ReviewActions row={row} onDone={onDone} />}
    </SidePanel>
  );
}

export default function EvidenceReviewPage() {
  const { role } = useAuth();
  const [params, setParams] = useSearchParams();
  const status = params.get('status') ?? 'pending';
  const page = parseInt(params.get('page') ?? '1', 10);
  const [selectedId, setSelectedId] = useState(null);
  const resource = useApiResource(
    withQuery('/api/m12/evidence-reviews', {
      status: status || undefined,
      page,
      page_size: PAGE_SIZE,
    }),
  );
  const columns = [
    {
      key: 'student',
      header: 'Sinh viên',
      rowHeader: true,
      render: (row) => `${row.student.name} (${row.student.code})`,
    },
    { key: 'skill', header: 'Kỹ năng, dự án', render: (row) => row.skill.name },
    {
      key: 'careers',
      header: 'Nghề, nhóm năng lực',
      render: (row) => <CareerGroups careers={row.careers} />,
    },
    { key: 'submitted', header: 'Ngày nộp', render: submittedText },
    {
      key: 'files',
      header: 'Tệp đính kèm',
      render: (row) =>
        row.attachments.length === 0 ? 'Không có' : <AttachmentList items={row.attachments} />,
    },
    { key: 'previous', header: 'Số lần nộp trước', render: (row) => row.previous_submissions },
    { key: 'status', header: 'Trạng thái', render: (row) => statusLabel(row.status) },
    {
      key: 'open',
      header: 'Xem',
      render: (row) => (
        <Button variant="ghost" size="sm" onClick={() => setSelectedId(row.id)}>
          Xem
        </Button>
      ),
    },
  ];
  return (
    <section className="m12-page">
      <PageHeader title="Duyệt minh chứng" />
      <div className="career-filter">
        <Select
          aria-label="Lọc theo trạng thái"
          className="career-filter__sort"
          value={status}
          onChange={(event) => setParams({ status: event.target.value })}
        >
          {STATUSES.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </Select>
      </div>
      <ResourceView
        resource={resource}
        loadingText="Đang tải minh chứng..."
        errorText="Không tải được minh chứng"
      >
        {(data) => {
          const selected = data.items.find((row) => row.id === selectedId);
          return data.items.length === 0 ? (
            <EmptyState title="Không có minh chứng nào" />
          ) : (
            <>
              <DataTable
                columns={columns}
                rows={data.items}
                rowKey={(row) => row.id}
                ariaLabel="Danh sách minh chứng"
              />
              <Pagination
                page={data.page}
                lastPage={Math.max(1, Math.ceil(data.total / data.page_size))}
                summary={`${data.total} minh chứng`}
                label="Phân trang minh chứng"
                onPage={(next) => setParams({ status, page: String(next) })}
              />
              {selected && (
                <ReviewPanel
                  row={selected}
                  canReview={role === 'advisor'}
                  onClose={() => setSelectedId(null)}
                  onDone={() => {
                    setSelectedId(null);
                    resource.retry();
                  }}
                />
              )}
            </>
          );
        }}
      </ResourceView>
    </section>
  );
}
