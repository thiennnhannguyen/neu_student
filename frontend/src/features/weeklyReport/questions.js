/**
 * 8 câu của báo cáo tuần (CR-12, D-312), khoảng 2 phút, phần lớn là chọn. Giá trị khớp
 * backend/app/services/weekly_report_rules.py. Không hỏi sức khỏe hay đời tư.
 */

export const PRIVACY_NOTE =
  'Câu trả lời dùng để phân tích tình hình học tập của bạn; cố vấn học tập được phân công có thể xem.';

export const NOTE_MAX = 300;

const LEVELS = [1, 2, 3, 4, 5].map((value) => ({ value, label: String(value) }));

export const QUESTIONS = [
  {
    name: 'attendance',
    label: 'Đi học tuần này',
    options: [
      { value: 'present', label: 'Có mặt' },
      { value: 'excused', label: 'Vắng có phép' },
      { value: 'absent', label: 'Vắng' },
    ],
  },
  {
    name: 'self_study',
    label: 'Thời gian tự học',
    options: [
      { value: 'none', label: '0 giờ' },
      { value: 'under_1h', label: 'Dưới 1 giờ' },
      { value: '1_2h', label: '1–2 giờ' },
      { value: '2_4h', label: '2–4 giờ' },
      { value: 'over_4h', label: 'Trên 4 giờ' },
    ],
  },
  {
    name: 'understanding',
    label: 'Mức hiểu bài tuần này',
    hint: '1 = chưa hiểu, 5 = hiểu rõ',
    options: LEVELS,
  },
  {
    name: 'unclear_note',
    label: 'Nội dung chưa hiểu',
    hint: `Không bắt buộc, tối đa ${NOTE_MAX} ký tự.`,
    note: true,
  },
  {
    name: 'assignment',
    label: 'Bài tập tuần này',
    options: [
      { value: 'done', label: 'Xong' },
      { value: 'in_progress', label: 'Đang làm' },
      { value: 'not_started', label: 'Chưa làm' },
      { value: 'no_assignment', label: 'Không có bài' },
    ],
  },
  {
    name: 'confidence',
    label: 'Mức tự tin nếu thi ngay bây giờ',
    hint: '1 = chưa tự tin, 5 = rất tự tin',
    options: LEVELS,
  },
  {
    name: 'obstacle',
    label: 'Cản trở nhiều nhất',
    options: [
      { value: 'busy_schedule', label: 'Lịch học dày' },
      { value: 'hard_content', label: 'Bài khó' },
      { value: 'lack_materials', label: 'Thiếu tài liệu' },
      { value: 'outside_work', label: 'Việc ngoài trường' },
      { value: 'none', label: 'Không có' },
    ],
  },
  {
    name: 'next_plan',
    label: 'Tuần tới định làm gì',
    options: [
      { value: 'review', label: 'Ôn lại bài' },
      { value: 'finish_assignments', label: 'Làm hết bài tập' },
      { value: 'ask_for_help', label: 'Hỏi giảng viên hoặc bạn' },
      { value: 'keep_going', label: 'Giữ như hiện tại' },
    ],
  },
];

export const REQUIRED = QUESTIONS.filter((question) => !question.note).map((q) => q.name);

/** Chữ của một câu trả lời đã lưu (xem lại chỉ đọc). */
export function answerLabel(name, value) {
  const question = QUESTIONS.find((item) => item.name === name);
  if (value === null || value === undefined || value === '') {
    return '—';
  }
  if (question.note) {
    return value;
  }
  return question.options.find((option) => option.value === value)?.label ?? String(value);
}

/** Câu bắt buộc chưa trả lời, theo thứ tự câu hỏi. */
export function missingAnswers(answers) {
  return REQUIRED.filter((name) => answers[name] === undefined || answers[name] === null);
}

export function reportKey(item) {
  return `${item.course.id}:${item.week.week_no}`;
}
