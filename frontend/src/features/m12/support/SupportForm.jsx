import { useState } from 'react';
import { useNavigate } from 'react-router';
import { apiRequest } from '../../../api/client';
import { Button, FormField, Input, Select, SidePanel, useToast } from '../../../components/ui';
import { ACCEPT_FILES } from '../AttachmentList';

const MAX_FILES = 3;

function errorsOf(cause) {
  const fields = cause.details?.fields;
  return fields ? Object.values(fields).flat() : [cause.message];
}

export default function SupportForm({ categories, onClose }) {
  const { show } = useToast();
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [categoryId, setCategoryId] = useState(categories[0]?.id ?? '');
  const [description, setDescription] = useState('');
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState([]);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setErrors([]);
    const body = new FormData();
    body.append('title', title);
    body.append('category_id', categoryId);
    body.append('description', description);
    [...files].forEach((file) => body.append('files', file));
    try {
      const created = await apiRequest('/api/m12/support-requests', { method: 'POST', body });
      show(`Đã gửi yêu cầu ${created.code}.`);
      navigate(`/m12/yeu-cau-ho-tro/${created.id}`);
    } catch (cause) {
      setErrors(errorsOf(cause));
      setBusy(false);
    }
  }

  return (
    <SidePanel title="Tạo yêu cầu hỗ trợ" onClose={onClose}>
      <form className="evidence-form" onSubmit={submit}>
        <FormField id="ticket-title" label="Tiêu đề">
          <Input
            id="ticket-title"
            required
            maxLength={255}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </FormField>
        <FormField id="ticket-category" label="Nhóm vấn đề">
          <Select
            id="ticket-category"
            value={categoryId}
            onChange={(event) => setCategoryId(event.target.value)}
          >
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </Select>
        </FormField>
        <FormField id="ticket-description" label="Mô tả">
          <textarea
            id="ticket-description"
            className="ui-input ui-textarea"
            rows={5}
            required
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </FormField>
        <FormField
          id="ticket-files"
          label="Tệp đính kèm (không bắt buộc)"
          hint={`Tối đa ${MAX_FILES} tệp pdf, png, jpg, jpeg, docx; mỗi tệp tối đa 5 MB.`}
        >
          <input
            id="ticket-files"
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
          Gửi yêu cầu
        </Button>
      </form>
    </SidePanel>
  );
}
