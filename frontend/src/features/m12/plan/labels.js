export const ASSUMED_POSITION = 'Vị trí theo giả định của nhóm – chờ xác minh';
export const DU_KIEN = 'Dự kiến – chưa xác minh lịch mở lớp';
export const CONFIRMED = 'Có lịch mở lớp';
export const ADDED_FOR_FLOOR = 'Thêm để đủ sàn tín chỉ';
export const NO_OFFERING_DATA = 'Chưa có lịch mở lớp – mọi kỳ là dự kiến';
export const PENDING_RESULT = 'Phụ thuộc kết quả';
export const PRIMARY_CAREER = 'Môn của nghề chính';
export const OUTSIDE_NOTE = 'Chỉ để tham khảo, không tính tín chỉ.';
export const OUTSIDE_TITLE = 'Môn của nghề ngoài CTĐT ngành bạn';
export const CURRENT_API = '/api/m12/roadmaps/current';
export const REGENERATE_WARNING = 'Các môn bạn đã chuyển tay sẽ bị xếp lại';

/** Chip so với HK của CTĐT. Môn CTĐT không ghi học kỳ thì không có chip. */
export function alignmentLabel(alignment) {
  if (!alignment) {
    return null;
  }
  if (alignment.kind === 'on_time') {
    return 'Đúng HK CTĐT';
  }
  const sign = alignment.offset > 0 ? '+' : '−';
  return `Lệch HK CTĐT (${sign}${Math.abs(alignment.offset)} kỳ)`;
}

export function prerequisiteStatus(status) {
  return { done: 'Đã đạt', in_progress: 'Đang học', not_done: 'Chưa đạt' }[status];
}

/** Chip lịch mở lớp chỉ có ích khi lộ trình có cả 2 loại. */
export function offeringSummary(items) {
  const confirmed = items.filter((item) => item.confidence === 'confirmed').length;
  return {
    showChip: confirmed > 0 && confirmed < items.length,
    allDuKien: items.length > 0 && confirmed === 0,
  };
}
