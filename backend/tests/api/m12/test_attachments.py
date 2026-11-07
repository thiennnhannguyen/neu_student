"""Tệp đính kèm: kiểm đuôi và nội dung, giới hạn, tên ngẫu nhiên, dọn tệp khi lỗi."""

import hashlib
import io
import zipfile
from pathlib import Path

import pytest
from flask import current_app
from werkzeug.datastructures import FileStorage

from app.common.errors import ApiError
from app.services import attachment_service as service

PDF = b"%PDF-1.7 noi dung mau"
PNG = b"\x89PNG\r\n\x1a\n noi dung"
JPG = b"\xff\xd8\xff noi dung"
EXE = b"MZ\x90\x00 chuong trinh"


def docx_bytes(with_marker=True):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml" if with_marker else "khac.txt", "x")
    return buffer.getvalue()


def upload(name, content):
    return FileStorage(stream=io.BytesIO(content), filename=name)


@pytest.mark.parametrize(
    ("name", "content", "kind"),
    [
        ("a.pdf", PDF, "application/pdf"),
        ("A.PDF", PDF, "application/pdf"),
        ("a.png", PNG, "image/png"),
        ("a.jpg", JPG, "image/jpeg"),
        ("a.jpeg", JPG, "image/jpeg"),
        (
            "a.docx",
            docx_bytes(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
    ],
)
def test_allowed_files(name, content, kind):
    checked = service.check_file(upload(name, content))

    assert checked.content_type == kind
    assert checked.size_bytes == len(content)
    assert checked.sha256 == hashlib.sha256(content).hexdigest()


@pytest.mark.parametrize(
    ("name", "content", "message"),
    [
        ("virus.pdf", EXE, "nội dung không đúng"),
        ("virus.exe", EXE, "chỉ nhận"),
        ("anh.png", PDF, "nội dung không đúng"),
        ("a.docx", docx_bytes(with_marker=False), "nội dung không đúng"),
        ("a.docx", b"PK\x03\x04 khong phai zip", "nội dung không đúng"),
        ("rong.pdf", b"", "tệp rỗng"),
        ("khongduoi", PDF, "chỉ nhận"),
        ("lon.pdf", PDF + b"x" * (6 * 1024 * 1024), "tối đa 5 MB"),
    ],
)
def test_rejected_files(name, content, message):
    with pytest.raises(ApiError) as caught:
        service.check_file(upload(name, content))

    assert caught.value.status == 422
    assert caught.value.code == "ATTACHMENT_INVALID"
    assert message in caught.value.message


def test_exactly_five_megabytes_is_allowed():
    content = PDF + b"x" * (5 * 1024 * 1024 - len(PDF))

    assert service.check_file(upload("a.pdf", content)).size_bytes == 5 * 1024 * 1024


def test_path_in_file_name_is_dropped():
    assert service.check_file(upload("../../etc/a.pdf", PDF)).original_name == "a.pdf"
    assert service.check_file(upload("C:\\tmp\\a.pdf", PDF)).original_name == "a.pdf"


def test_too_many_files():
    files = [upload(f"{n}.pdf", PDF) for n in range(3)]

    with pytest.raises(ApiError) as caught:
        service.check_files(files, 2)
    assert caught.value.message == "Tối đa 2 tệp."


def test_empty_file_field_is_ignored():
    assert service.check_files([FileStorage(stream=io.BytesIO(b""), filename="")], 2) == []


def test_store_uses_random_name_and_cleans_up_on_error(seeded_app):
    checked = service.check_file(upload("bao cao.pdf", PDF))
    folder = Path(current_app.config["UPLOAD_DIR"])

    with pytest.raises(RuntimeError):
        with service.storing_files() as stored:
            name = stored.store(checked)
            assert "bao" not in name
            assert name.endswith(".pdf")
            assert (folder / name).read_bytes() == PDF
            raise RuntimeError("lỗi giữa chừng")

    assert not (folder / name).exists()


def test_upload_folder_is_outside_app_and_ignored_by_git():
    root = Path(__file__).resolve().parents[3]

    assert "backend/uploads/" in (root.parent / ".gitignore").read_text(encoding="utf8")


def test_clean_uploads_command(seeded_app):
    folder = Path(current_app.config["UPLOAD_DIR"])
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "thua.pdf").write_bytes(PDF)
    (folder / "thu-muc").mkdir(exist_ok=True)

    result = current_app.test_cli_runner().invoke(args=["clean-uploads"])

    assert result.exit_code == 0
    assert "Đã xóa" in result.output
    assert not (folder / "thua.pdf").exists()


def test_clean_uploads_refused_in_production(seeded_app, monkeypatch):
    monkeypatch.setitem(current_app.config, "APP_CONFIG_NAME", "production")

    result = current_app.test_cli_runner().invoke(args=["clean-uploads"])

    assert result.exit_code != 0
    assert "production" in result.output
