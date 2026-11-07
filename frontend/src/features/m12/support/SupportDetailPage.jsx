import { useState } from 'react';
import { useParams } from 'react-router';
import { apiRequest } from '../../../api/client';
import { Button, FormField, PageHeader, useToast } from '../../../components/ui';
import useApiResource from '../../m11/useApiResource';
import { ResourceView } from '../../m11/ui';
import AttachmentList, { ACCEPT_FILES } from '../AttachmentList';
import TicketStatus, { statusLabel } from './TicketStatus';

const TIME_FORMAT = new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short', timeStyle: 'short' });
const MAX_FILES = 3;

function timeText(value) {
  return TIME_FORMAT.format(new Date(value));
}

function Thread({ messages }) {
  return (
    <ol className="ticket-thread">
      {messages.map((message) => (
        <li
          key={message.id}
          className={`ticket-message${message.is_mine ? ' ticket-message--mine' : ''}`}
        >
          <p className="ticket-message__head">
            <strong>{message.author}</strong>
            <time dateTime={message.created_at}>{timeText(message.created_at)}</time>
          </p>
          <p className="ticket-message__body">{message.body}</p>
          <AttachmentList items={message.attachments} />
        </li>
      ))}
    </ol>
  );
}

function Timeline({ ticket }) {
  return (
    <ol className="ticket-timeline">
      <li>
        <strong>Tạo yêu cầu</strong>
        <time dateTime={ticket.created_at}>{timeText(ticket.created_at)}</time>
      </li>
      {ticket.timeline.map((event) => (
        <li key={`${event.created_at}-${event.to_status}`}>
          <strong>{event.to_label}</strong>
          <span>{event.actor}</span>
          <time dateTime={event.created_at}>{timeText(event.created_at)}</time>
        </li>
      ))}
    </ol>
  );
}

function ReplyForm({ ticketId, onDone }) {
  const [body, setBody] = useState('');
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    const form = new FormData();
    form.append('body', body);
    [...files].forEach((file) => form.append('files', file));
    try {
      await apiRequest(`/api/m12/support-requests/${ticketId}/messages`, {
        method: 'POST',
        body: form,
      });
      onDone();
    } catch (cause) {
      setError(cause.details?.fields?.files?.[0] ?? cause.message);
      setBusy(false);
    }
  }

  return (
    <form className="evidence-form ticket-reply" onSubmit={submit}>
      <FormField id="ticket-reply" label="Trả lời">
        <textarea
          id="ticket-reply"
          className="ui-input ui-textarea"
          rows={3}
          required
          value={body}
          onChange={(event) => setBody(event.target.value)}
        />
      </FormField>
      <FormField
        id="ticket-reply-files"
        label="Tệp đính kèm (không bắt buộc)"
        hint={`Tối đa ${MAX_FILES} tệp, mỗi tệp tối đa 5 MB.`}
      >
        <input
          id="ticket-reply-files"
          type="file"
          multiple
          accept={ACCEPT_FILES}
          onChange={(event) => setFiles(event.target.files)}
        />
      </FormField>
      {error && (
        <p role="alert" className="status-error">
          {error}
        </p>
      )}
      <Button type="submit" loading={busy}>
        Gửi
      </Button>
    </form>
  );
}

function StatusActions({ ticket, onDone }) {
  const { show } = useToast();
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  async function change(status) {
    setBusy(status);
    setError('');
    try {
      await apiRequest(`/api/m12/support-requests/${ticket.id}/status`, {
        method: 'POST',
        body: { status },
      });
      show(`Đã chuyển sang ${statusLabel(status)}.`);
      onDone();
    } catch (cause) {
      setError(cause.message);
      setBusy('');
    }
  }

  return (
    <div className="ticket-status-actions">
      {ticket.next_statuses.map((status) => (
        <Button
          key={status}
          variant="secondary"
          size="sm"
          loading={busy === status}
          onClick={() => change(status)}
        >
          Chuyển sang {statusLabel(status)}
        </Button>
      ))}
      {error && (
        <p role="alert" className="status-error">
          {error}
        </p>
      )}
    </div>
  );
}

function Ticket({ ticket, reload }) {
  return (
    <div className="ticket-detail">
      <div className="ticket-detail__main">
        <p className="ticket-detail__meta">
          <span>{ticket.code}</span>
          <span>{ticket.category.name}</span>
          <span>
            {ticket.student.name} ({ticket.student.code})
          </span>
          <TicketStatus status={ticket.status} />
        </p>
        <h2>{ticket.title}</h2>
        <Thread messages={ticket.messages} />
        {ticket.can_reply && (
          <ReplyForm key={ticket.updated_at} ticketId={ticket.id} onDone={reload} />
        )}
        {!ticket.can_reply && ticket.status !== 'done' && ticket.next_statuses.length === 0 && (
          <p className="evidence-note">
            Bạn chỉ trả lời được khi yêu cầu ở trạng thái Cần bổ sung.
          </p>
        )}
        {ticket.status === 'done' && (
          <p className="evidence-note">
            Yêu cầu đã hoàn thành. Cần hỗ trợ thêm thì tạo yêu cầu mới.
          </p>
        )}
      </div>
      <aside className="ticket-detail__side" aria-label="Trạng thái yêu cầu">
        <h3>Tiến trình</h3>
        <Timeline ticket={ticket} />
        {ticket.next_statuses.length > 0 && <StatusActions ticket={ticket} onDone={reload} />}
      </aside>
    </div>
  );
}

export default function SupportDetailPage() {
  const { id } = useParams();
  const resource = useApiResource(`/api/m12/support-requests/${id}`);
  return (
    <section className="m12-page">
      <PageHeader title="Chi tiết yêu cầu" />
      <p>
        <Button variant="ghost" size="sm" to="/m12/yeu-cau-ho-tro">
          Về danh sách
        </Button>
      </p>
      <ResourceView
        resource={resource}
        loadingText="Đang tải yêu cầu..."
        errorText="Không tải được yêu cầu"
      >
        {(ticket) => <Ticket ticket={ticket} reload={resource.retry} />}
      </ResourceView>
    </section>
  );
}
