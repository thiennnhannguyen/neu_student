"""Lệnh quản trị. Không chứa nghiệp vụ hay SQL; mọi xử lý nằm trong service."""

import click
from flask import Flask
from flask.cli import AppGroup

from app.common.course_display import course_display_code
from app.common.errors import ApiError
from app.common.transaction import transaction
from app.extensions import db
from app.models.shared import Course
from app.services import attachment_service
from app.services.grades_service import DEFAULT_ACTOR, add_grade_result

grades_cli = AppGroup("grades", help="Quản lý kết quả học phần mẫu.")


@grades_cli.command("add")
@click.option("--student", required=True, help="Mã sinh viên, ví dụ SV05.")
@click.option("--course", required=True, help="Id học phần, ví dụ CNT101.")
@click.option("--semester", required=True, help="Id học kỳ, ví dụ S3.")
@click.option("--score", required=True, help="Điểm 0–10, tối đa 1 chữ số thập phân.")
@click.option("--actor", default=DEFAULT_ACTOR, show_default=True, help="Tài khoản admin.")
def add_grade(student, course, semester, score, actor):
    """Thêm kết quả học phần mẫu."""
    try:
        with transaction():
            result = add_grade_result(student, course, semester, score, actor)
    except ApiError as error:
        raise click.ClickException(error.message) from error

    attempt = result.attempt
    code = course_display_code(db.session.get(Course, attempt.course_id).code)
    click.echo(
        f"Đã thêm: {student} {code} kỳ {attempt.semester_id}: "
        f"{attempt.score_10} -> {attempt.letter} ({attempt.grade_4})"
    )
    for warning in result.warnings:
        click.echo(f"Cảnh báo: {warning}")


def register_grades_command(app: Flask) -> None:
    app.cli.add_command(grades_cli)


def register_clean_uploads_command(app: Flask) -> None:
    @app.cli.command("clean-uploads", help="Xóa tệp tải lên ở máy dev, dùng sau khi seed lại.")
    def clean_uploads():
        try:
            click.echo(f"Đã xóa {attachment_service.clean_all()} tệp.")
        except ApiError as error:
            raise click.ClickException(error.message) from error
