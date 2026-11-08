/**
 * D-313: tên và cách tính của điểm bài tập hiện tại, điểm quá trình hiện tại. Dùng chung cho trang
 * Phân tích & Cảnh báo và form LMS Demo; số do backend tính (lms_service.summarize).
 */
import { InfoPopover } from '../../components/ui';

export const ASSIGNMENT_SCORE = 'Điểm bài tập hiện tại';
export const PROCESS_SCORE = 'Điểm quá trình hiện tại';
export const TEST_SCORE = 'Điểm kiểm tra';

export const ASSIGNMENT_SCORE_HELP =
  'Trung bình có trọng số của bài đã chấm và bài quá hạn chưa nộp (tính 0 điểm). Bài chưa tới hạn và bài đã nộp đang chờ chấm chưa tính. Bài nộp muộn giữ điểm, trừ điểm nộp muộn theo cấu hình (mặc định không trừ).';
export const PROCESS_SCORE_HELP =
  'Gộp các bài tập ở trên với bài kiểm tra, giữa kỳ đã có điểm, theo trọng số của từng mục. Đây là phần điểm quá trình, chưa phải điểm môn.';

export function ScoreHelp() {
  return (
    <InfoPopover label="Cách tính điểm bài tập và điểm quá trình">
      <p>
        <strong>{ASSIGNMENT_SCORE}:</strong> {ASSIGNMENT_SCORE_HELP}
      </p>
      <p>
        <strong>{PROCESS_SCORE}:</strong> {PROCESS_SCORE_HELP}
      </p>
    </InfoPopover>
  );
}
