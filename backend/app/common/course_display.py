"""Hiển thị học phần. courses.id là khóa kỹ thuật, không bao giờ được dùng thay cho mã môn."""

NO_CODE_LABEL = "Chưa có mã"


def course_display_code(code: str | None) -> str:
    return code if code else NO_CODE_LABEL
