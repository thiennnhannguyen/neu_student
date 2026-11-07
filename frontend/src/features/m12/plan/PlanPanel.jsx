import { useState } from 'react';
import { apiRequest } from '../../../api/client';
import { Button, FormField, Select, SidePanel, useToast } from '../../../components/ui';
import { NO_CODE } from '../labels';
import { ADDED_FOR_FLOOR, ASSUMED_POSITION, prerequisiteStatus } from './labels';

function violationsOf(cause) {
  const rows = cause.details?.violations;
  return rows?.length ? rows.map((row) => row.message) : [cause.message];
}

function MoveForm({ roadmap, item, onMoved }) {
  const { show } = useToast();
  const current = roadmap.semesters.find((column) =>
    column.items.some((row) => row.id === item.id),
  );
  const options = roadmap.semesters.filter((column) => column.id !== current?.id);
  const [semesterId, setSemesterId] = useState(options[0]?.id ?? '');
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState([]);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setErrors([]);
    try {
      await apiRequest(`/api/m12/roadmaps/${roadmap.id}/items/${item.id}`, {
        method: 'PATCH',
        body: { semester_id: semesterId },
      });
      show(`Đã chuyển ${item.course.name}.`);
      onMoved();
    } catch (cause) {
      setErrors(violationsOf(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="plan-panel__move" onSubmit={submit}>
      <FormField label="Chuyển sang kỳ…" id="plan-move-semester">
        <Select
          id="plan-move-semester"
          value={semesterId}
          onChange={(event) => setSemesterId(event.target.value)}
        >
          {options.map((column) => (
            <option key={column.id} value={column.id}>
              {column.name}
            </option>
          ))}
        </Select>
      </FormField>
      <Button type="submit" variant="secondary" loading={busy} disabled={options.length === 0}>
        Chuyển kỳ
      </Button>
      {errors.length > 0 && (
        <div role="alert" className="status-error">
          <strong>Không chuyển được:</strong>
          <ul>
            {errors.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        </div>
      )}
    </form>
  );
}

/** Lý do xếp, tiên quyết chính thức, chuyển kỳ. Chỉ sinh viên có ô chuyển kỳ. */
export default function PlanPanel({ roadmap, item, canEdit, inline, onClose, onMoved }) {
  return (
    <SidePanel title={item.course.name} onClose={onClose} inline={inline}>
      <p className="plan-panel__meta">
        {item.course.code ?? NO_CODE} · {item.course.credits} tín chỉ
      </p>
      <h3>Lý do xếp</h3>
      <p>{item.reason}</p>
      {item.added_for_floor && <p className="plan-card__assumed">{ADDED_FOR_FLOOR}</p>}
      {item.assumed_position && <p className="plan-card__assumed">{ASSUMED_POSITION}</p>}
      <h3>Tiên quyết</h3>
      {item.prerequisites.length === 0 ? (
        <p>Không có tiên quyết chính thức.</p>
      ) : (
        <ul className="plan-panel__prerequisites">
          {item.prerequisites.map((row) => (
            <li key={row.course_id}>
              {row.name} ({row.code ?? NO_CODE}): {prerequisiteStatus(row.status)}
            </li>
          ))}
        </ul>
      )}
      {canEdit && <MoveForm roadmap={roadmap} item={item} onMoved={onMoved} />}
    </SidePanel>
  );
}
