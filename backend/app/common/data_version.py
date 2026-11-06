"""Phiên bản dữ liệu của sinh viên. Khóa cache kết quả đọc giá trị này.

Mọi thao tác ghi làm đổi kết quả M11 hoặc M12 của sinh viên (điểm, nghề chính, minh chứng kỹ năng)
phải gọi hàm này trong cùng transaction.
"""

from app.extensions import db
from app.models.shared import Student


def bump_data_version(student: Student) -> None:
    """Tăng bằng phép tính trong SQL để hai request đồng thời không ghi đè nhau."""
    student.data_version = Student.data_version + 1
    db.session.flush()
