import { useState } from 'react';
import { apiRequest } from '../../../api/client';
import {
  Button,
  FormField,
  Input,
  SidePanel,
  StatusChip,
  StatusLegend,
  useToast,
} from '../../../components/ui';
import { withQuery } from '../../m11/format';
import useApiResource from '../../m11/useApiResource';
import { ResourceView } from '../../m11/ui';
import AttachmentList, { ACCEPT_FILES } from '../AttachmentList';

const DESCRIPTION_MAX = 1000;
const MAX_FILES = 2;
const OPEN_STATUSES = ['pending', 'approved'];

function statusOf(row) {
  return row.status === 'rejected' ? 'failed' : row.status === 'approved' ? 'done' : 'pending';
}

function errorsOf(cause) {
  const fields = cause.details?.fields;
  return fields ? Object.values(fields).flat() : [cause.message];
}

function SubmitForm({ skillId, onDone }) {
  const { show } = useToast();
  const [description, setDescription] = useState('');
  const [link, setLink] = useState('');
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState([]);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setErrors([]);
    const body = new FormData();
    body.append('skill_id', skillId);
    body.append('description', description);
    body.append('link', link);
    [...files].forEach((file) => body.append('files', file));
    try {
      await apiRequest('/api/m12/evidences', { method: 'POST', body });
      show('Đã nộp minh chứng, đang chờ cố vấn duyệt.');
      onDone();
    } catch (cause) {
      setErrors(errorsOf(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="evidence-form" onSubmit={submit}>
      <FormField id="evidence-description" label="Mô tả" hint={`Tối đa ${DESCRIPTION_MAX} ký tự.`}>
        <textarea
          id="evidence-description"
          className="ui-input ui-textarea"
          rows={4}
          required
          maxLength={DESCRIPTION_MAX}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
      </FormField>
      <FormField id="evidence-link" label="Liên kết (không bắt buộc)">
        <Input
          id="evidence-link"
          type="url"
          placeholder="https://"
          value={link}
          onChange={(event) => setLink(event.target.value)}
        />
      </FormField>
      <FormField
        id="evidence-files"
        label="Tệp đính kèm (không bắt buộc)"
        hint={`Tối đa ${MAX_FILES} tệp pdf, png, jpg, jpeg, docx; mỗi tệp tối đa 5 MB.`}
      >
        <input
          id="evidence-files"
          type="file"
          multiple
          accept={ACCEPT_FILES}
          onChange={(event) => setFiles(event.target.files)}
        />
      </FormField>
      {errors.length > 0 && (
        <div role="alert" className="status-error">
          {errors.map((message) => (
            <p key={message}>{message}</p>
          ))}
        </div>
      )}
      <Button type="submit" loading={busy}>
        Nộp minh chứng
      </Button>
    </form>
  );
}

function History({ rows }) {
  if (rows.length === 0) {
    return <p>Chưa có minh chứng.</p>;
  }
  return (
    <>
      <StatusLegend statuses={['done', 'pending', 'failed']} />
      <ul className="evidence-history">
        {rows.map((row) => (
          <li key={row.id}>
            <StatusChip status={statusOf(row)} />
            {row.status === 'approved' && <span className="evidence-history__tag">Đã duyệt</span>}
            {row.status === 'rejected' && <span className="evidence-history__tag">Bị từ chối</span>}
            <p>{row.description}</p>
            {row.link && (
              <p>
                <a href={row.link} target="_blank" rel="noreferrer">
                  {row.link}
                </a>
              </p>
            )}
            {row.review_note && (
              <p>
                <strong>Nhận xét: </strong>
                {row.review_note}
              </p>
            )}
            <AttachmentList items={row.attachments} />
          </li>
        ))}
      </ul>
    </>
  );
}

/** Minh chứng gắn với kỹ năng nên kỹ năng dùng chung nhiều nghề chỉ cần nộp 1 lần. */
export default function EvidencePanel({ child, student, onClose, onChanged }) {
  const resource = useApiResource(
    withQuery('/api/m12/evidences', { ...student.query, skill_id: child.skill_id }),
  );
  return (
    <SidePanel title={child.title} onClose={onClose}>
      <p className="evidence-note">
        Hoàn thành kỹ năng, dự án chỉ tính khi minh chứng đã được cố vấn duyệt.
      </p>
      <ResourceView
        compact
        resource={resource}
        loadingText="Đang tải minh chứng..."
        errorText="Không tải được minh chứng"
      >
        {(data) => {
          const canSubmit =
            student.isStudent && !data.items.some((row) => OPEN_STATUSES.includes(row.status));
          return (
            <>
              <h3>Lịch sử</h3>
              <History rows={data.items} />
              {canSubmit && (
                <>
                  <h3>Nộp minh chứng mới</h3>
                  <SubmitForm
                    skillId={child.skill_id}
                    onDone={() => {
                      resource.retry();
                      onChanged();
                    }}
                  />
                </>
              )}
            </>
          );
        }}
      </ResourceView>
    </SidePanel>
  );
}
