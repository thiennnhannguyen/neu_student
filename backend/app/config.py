"""Cấu hình ứng dụng theo môi trường."""

import os
import tempfile
from datetime import timedelta
from pathlib import Path


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-khong-dung-o-production"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///neu_student.db"
    TESTING = False
    DEBUG = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    # Bài kiểm tra mô-đun (CR-04).
    QUIZ_QUESTION_COUNT = int(os.environ.get("QUIZ_QUESTION_COUNT", "10"))
    QUIZ_DURATION_MINUTES = int(os.environ.get("QUIZ_DURATION_MINUTES", "15"))
    QUIZ_PASS_PERCENT = int(os.environ.get("QUIZ_PASS_PERCENT", "80"))
    QUIZ_RETRY_COOLDOWN_MINUTES = int(os.environ.get("QUIZ_RETRY_COOLDOWN_MINUTES", "10"))
    # D-309: ngày "hôm nay" của hệ thống cho demo (YYYY-MM-DD). Không đặt thì dùng ngày thật.
    DEMO_TODAY = os.environ.get("DEMO_TODAY") or None
    # D-313: điểm trừ mỗi bài tập nộp muộn (chuỗi thập phân, hệ 10); mặc định không trừ.
    LMS_LATE_PENALTY = os.environ.get("LMS_LATE_PENALTY") or "0"
    # Hết hạn sau 2 giờ không hoạt động: cookie được ký lại ở mỗi request.
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_REFRESH_EACH_REQUEST = True
    # Ngoài thư mục phục vụ web, có trong .gitignore. Tệp chỉ tải được qua API có kiểm quyền.
    UPLOAD_DIR = os.environ.get("UPLOAD_DIR") or str(
        Path(__file__).resolve().parents[1] / "uploads"
    )
    # 3 tệp, mỗi tệp 5 MB, cộng phần còn lại của form. Tệp lẻ quá 5 MB được service báo riêng.
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    # Bản build của giao diện, Flask phục vụ ở cùng cổng với API.
    FRONTEND_DIST = os.environ.get("FRONTEND_DIST") or str(
        Path(__file__).resolve().parents[2] / "frontend" / "dist"
    )


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = "test-only"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    UPLOAD_DIR = tempfile.mkdtemp(prefix="neu-student-upload-test-")


class ProductionConfig(BaseConfig):
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SESSION_COOKIE_SECURE = True


class LocalProdConfig(ProductionConfig):
    """Bản build chạy trên máy cá nhân qua http://localhost. Không dùng để triển khai thật.

    Cookie vẫn Secure trừ khi biến môi trường SESSION_COOKIE_SECURE ghi rõ false (D-275).
    """


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "local-prod": LocalProdConfig,
}
