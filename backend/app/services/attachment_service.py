"""Tệp đính kèm dùng chung cho minh chứng và ticket. Không đọc DB, không kiểm quyền."""

import hashlib
import io
import uuid
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from flask import current_app, send_from_directory
from werkzeug.datastructures import FileStorage

from app.common.errors import ApiError

MAX_BYTES = 5 * 1024 * 1024
ORIGINAL_NAME_MAX = 255
DOCX_MARKER = "word/document.xml"
# Đuôi -> (loại nội dung lưu lại, byte đầu tệp phải có).
ALLOWED = {
    ".pdf": ("application/pdf", b"%PDF-"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        b"PK\x03\x04",
    ),
}


@dataclass(frozen=True)
class CheckedFile:
    original_name: str
    extension: str
    content_type: str
    size_bytes: int
    sha256: str
    content: bytes


def _reject(message: str) -> ApiError:
    return ApiError(
        422, message=message, code="ATTACHMENT_INVALID", details={"fields": {"files": [message]}}
    )


def _is_docx(content: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            return DOCX_MARKER in archive.namelist()
    except zipfile.BadZipFile:
        return False


def check_file(file: FileStorage) -> CheckedFile:
    """Kiểm cả đuôi lẫn nội dung: đổi đuôi một tệp .exe thành .pdf vẫn bị từ chối."""
    name = Path((file.filename or "").replace("\\", "/")).name
    extension = Path(name).suffix.lower()
    if extension not in ALLOWED:
        raise _reject(f"{name or 'Tệp'}: chỉ nhận pdf, png, jpg, jpeg, docx.")
    content = file.stream.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise _reject(f"{name}: tối đa 5 MB.")
    if not content:
        raise _reject(f"{name}: tệp rỗng.")
    content_type, magic = ALLOWED[extension]
    if not content.startswith(magic) or (extension == ".docx" and not _is_docx(content)):
        raise _reject(f"{name}: nội dung không đúng định dạng {extension[1:]}.")
    return CheckedFile(
        original_name=name[-ORIGINAL_NAME_MAX:],
        extension=extension,
        content_type=content_type,
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        content=content,
    )


def check_files(files: list[FileStorage], limit: int) -> list[CheckedFile]:
    chosen = [file for file in files if file.filename]
    if len(chosen) > limit:
        raise _reject(f"Tối đa {limit} tệp.")
    return [check_file(file) for file in chosen]


def _folder() -> Path:
    folder = Path(current_app.config["UPLOAD_DIR"])
    folder.mkdir(parents=True, exist_ok=True)
    return folder


class StoredFiles:
    """Ghi tệp với tên ngẫu nhiên, nhớ lại để xóa nếu transaction thất bại."""

    def __init__(self):
        self.paths: list[Path] = []

    def store(self, file: CheckedFile) -> str:
        stored_name = f"{uuid.uuid4().hex}{file.extension}"
        path = _folder() / stored_name
        path.write_bytes(file.content)
        self.paths.append(path)
        return stored_name

    def remove_all(self) -> None:
        for path in self.paths:
            path.unlink(missing_ok=True)


@contextmanager
def storing_files():
    """Bọc ngoài `with transaction()`: lỗi ở bất kỳ đâu thì không để lại tệp mồ côi."""
    stored = StoredFiles()
    try:
        yield stored
    except Exception:
        stored.remove_all()
        raise


def send_stored(stored_name: str, original_name: str, content_type: str):
    """Luôn tải về, không mở trong trình duyệt; tệp mất trên đĩa thì 404."""
    response = send_from_directory(
        _folder(),
        stored_name,
        as_attachment=True,
        download_name=original_name,
        mimetype=content_type,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def attachment_json(row, url: str) -> dict:
    return {
        "id": row.id,
        "original_name": row.original_name,
        "content_type": row.content_type,
        "size_bytes": row.size_bytes,
        "url": url,
    }


def clean_all() -> int:
    """Chỉ dùng ở dev sau khi seed lại, khi không còn bản ghi nào trỏ tới tệp."""
    if current_app.config["APP_CONFIG_NAME"] == "production":
        raise ApiError(403, message="Không được xóa tệp ở production.")
    removed = 0
    for path in _folder().iterdir():
        if path.is_file():
            path.unlink()
            removed += 1
    return removed
