"""Bài kiểm tra mô-đun và chứng chỉ số (CR-04). Chấm ở server, đáp án chỉ lộ sau khi nộp."""

import random
import secrets
from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.common import clock
from app.common.auth_guard import can_access_student
from app.common.data_version import bump_data_version
from app.common.errors import ApiError
from app.extensions import db
from app.models.m12 import (
    CareerModule,
    Certificate,
    QuizAttempt,
    QuizAttemptQuestion,
    QuizOption,
    QuizQuestion,
    SkillEvidence,
)
from app.models.shared import ProgramVersion, Student, User
from app.services.career_api_service import iso_time

IN_PROGRESS = "in_progress"
SUBMITTED = "submitted"
EXPIRED = "expired"
APPROVED = "approved"
SINGLE_ANSWER_KINDS = ("single", "code", "http")
AUTHOR_LABEL = "Câu hỏi do nhóm biên soạn"
CERTIFICATE_NOTICE = (
    "Chứng nhận hoàn thành bài kiểm tra trên nền tảng bài tập lớn – "
    "không phải chứng chỉ của Trường Đại học Kinh tế Quốc dân."
)
_random = random.SystemRandom()


def _config(name: str) -> int:
    return current_app.config[name]


def _module_for(student: Student, module_id: str) -> CareerModule:
    """Mô-đun của nghề thuộc đúng ngành sinh viên. Khác ngành thì coi như không tồn tại."""
    module = db.session.get(CareerModule, module_id)
    program_id = db.session.scalar(
        select(ProgramVersion.program_id).where(ProgramVersion.id == student.program_version_id)
    )
    if module is None or module.program_id != program_id:
        raise ApiError(404)
    return module


def _student_of(user: User) -> Student:
    """Route đã giới hạn vai trò sinh viên."""
    return db.session.scalars(select(Student).where(Student.user_id == user.id)).one()


def _own_attempt(user: User, attempt_id: str) -> QuizAttempt:
    attempt = db.session.get(QuizAttempt, attempt_id)
    student = _student_of(user)
    if attempt is None or attempt.student_id != student.id:
        raise ApiError(404)
    return attempt


def _attempt_rows(attempt: QuizAttempt) -> list[QuizAttemptQuestion]:
    return list(
        db.session.scalars(
            select(QuizAttemptQuestion)
            .where(QuizAttemptQuestion.attempt_id == attempt.id)
            .order_by(QuizAttemptQuestion.order)
        )
    )


def _questions_of(rows: list[QuizAttemptQuestion]) -> dict[str, QuizQuestion]:
    ids = [row.question_id for row in rows]
    return {
        q.id: q for q in db.session.scalars(select(QuizQuestion).where(QuizQuestion.id.in_(ids)))
    }


def _options_of(question_ids: list[str]) -> dict[str, list[QuizOption]]:
    found: dict[str, list[QuizOption]] = {}
    rows = db.session.scalars(
        select(QuizOption)
        .where(QuizOption.question_id.in_(question_ids))
        .order_by(QuizOption.order)
    )
    for row in rows:
        found.setdefault(row.question_id, []).append(row)
    return found


def _open_json(attempt: QuizAttempt, module: CareerModule) -> dict:
    """Không có is_correct và explanation: đáp án không xuống trình duyệt trước khi nộp."""
    rows = _attempt_rows(attempt)
    questions = _questions_of(rows)
    options = _options_of(list(questions))
    now = clock.utcnow()
    return {
        "id": attempt.id,
        "status": attempt.status,
        "module": {"id": module.id, "order": module.order, "title": module.title},
        "attempt_no": attempt.attempt_no,
        "started_at": iso_time(attempt.started_at),
        "deadline_at": iso_time(attempt.deadline_at),
        "remaining_seconds": max(0, int((attempt.deadline_at - now).total_seconds())),
        "total": attempt.total,
        "author_label": AUTHOR_LABEL,
        "questions": [
            {
                "id": row.question_id,
                "order": row.order,
                "kind": questions[row.question_id].kind,
                "prompt": questions[row.question_id].prompt,
                "code": questions[row.question_id].code_snippet,
                "options": [
                    {"id": option.id, "text": option.text}
                    for option_id in row.option_order
                    for option in options[row.question_id]
                    if option.id == option_id
                ],
                "selected_option_ids": row.selected_option_ids or [],
            }
            for row in rows
        ],
    }


def _reviewed_questions(rows: list[QuizAttemptQuestion]) -> list[dict]:
    questions = _questions_of(rows)
    options = _options_of(list(questions))
    return [
        {
            "id": row.question_id,
            "order": row.order,
            "kind": questions[row.question_id].kind,
            "prompt": questions[row.question_id].prompt,
            "code": questions[row.question_id].code_snippet,
            "options": [
                {"id": option.id, "text": option.text, "is_correct": option.is_correct}
                for option_id in row.option_order
                for option in options[row.question_id]
                if option.id == option_id
            ],
            "selected_option_ids": row.selected_option_ids or [],
            "is_correct": row.is_correct,
            "explanation": questions[row.question_id].explanation,
        }
        for row in rows
    ]


def _certificate_json(row: Certificate) -> dict:
    return {
        "code": row.code,
        "module_id": row.module_id,
        "student_name": row.student_name,
        "module_title": row.module_title,
        "correct_count": row.correct_count,
        "total": row.total,
        "percent": _percent(row.correct_count, row.total),
        "issued_at": iso_time(row.issued_at),
        "valid": row.revoked_at is None,
        "notice": CERTIFICATE_NOTICE,
    }


def _percent(correct: int, total: int) -> int:
    return correct * 100 // total


def _is_pass(correct: int, total: int) -> bool:
    return correct * 100 >= _config("QUIZ_PASS_PERCENT") * total


def _retry_at(attempt: QuizAttempt) -> datetime | None:
    """Lượt quá hạn tính từ lúc hết giờ, không tính từ lúc server phát hiện ra."""
    if attempt.met_threshold:
        return None
    ended = attempt.submitted_at or attempt.deadline_at
    return ended + timedelta(minutes=_config("QUIZ_RETRY_COOLDOWN_MINUTES"))


def _result_json(attempt: QuizAttempt, module: CareerModule) -> dict:
    certificate = db.session.scalar(select(Certificate).where(Certificate.attempt_id == attempt.id))
    return {
        "id": attempt.id,
        "status": attempt.status,
        "module": {"id": module.id, "order": module.order, "title": module.title},
        "attempt_no": attempt.attempt_no,
        "correct_count": attempt.correct_count,
        "total": attempt.total,
        "percent": _percent(attempt.correct_count, attempt.total),
        "pass_percent": _config("QUIZ_PASS_PERCENT"),
        "passed": attempt.met_threshold,
        "auto_submitted": attempt.status == EXPIRED,
        "submitted_at": iso_time(attempt.submitted_at),
        "retry_at": iso_time(_retry_at(attempt)),
        "certificate": _certificate_json(certificate) if certificate else None,
        "author_label": AUTHOR_LABEL,
        "questions": _reviewed_questions(_attempt_rows(attempt)),
    }


def _close(attempt: QuizAttempt, status: str, now: datetime) -> bool:
    """Chỉ một request đóng được lượt: UPDATE có điều kiện, không đọc rồi ghi."""
    closed = db.session.execute(
        update(QuizAttempt)
        .where(QuizAttempt.id == attempt.id, QuizAttempt.status == IN_PROGRESS)
        .values(status=status, submitted_at=now)
    )
    if closed.rowcount == 0:
        return False
    db.session.refresh(attempt)
    _grade(attempt, now)
    return True


def _grade(attempt: QuizAttempt, now: datetime) -> None:
    rows = _attempt_rows(attempt)
    options = _options_of([row.question_id for row in rows])
    correct = 0
    for row in rows:
        expected = {o.id for o in options[row.question_id] if o.is_correct}
        row.is_correct = set(row.selected_option_ids or []) == expected
        correct += row.is_correct
    attempt.correct_count = correct
    attempt.met_threshold = _is_pass(correct, attempt.total)
    if attempt.met_threshold:
        _issue_certificate(attempt, now)


def _issue_certificate(attempt: QuizAttempt, now: datetime) -> None:
    module = db.session.get(CareerModule, attempt.module_id)
    student = db.session.get(Student, attempt.student_id)
    db.session.add(
        Certificate(
            code=secrets.token_urlsafe(18),
            student_id=student.id,
            module_id=module.id,
            attempt_id=attempt.id,
            student_name=db.session.get(User, student.user_id).full_name,
            module_title=module.title,
            correct_count=attempt.correct_count,
            total=attempt.total,
            issued_at=now,
        )
    )
    db.session.add(
        SkillEvidence(
            student_id=student.id,
            skill_id=module.skill_id,
            description=f"Đạt bài kiểm tra mô-đun: {module.title}",
            status=APPROVED,
            source="quiz",
            submitted_at=now,
            reviewed_at=now,
        )
    )
    bump_data_version(student)
    db.session.flush()


def _expire_if_late(attempt: QuizAttempt) -> None:
    """Hết giờ: tự nộp theo đáp án đã lưu, kể cả khi trình duyệt đã đóng."""
    now = clock.utcnow()
    if attempt.status == IN_PROGRESS and now >= attempt.deadline_at:
        _close(attempt, EXPIRED, attempt.deadline_at)


def _expire_open_attempts(student: Student, module: CareerModule) -> None:
    attempt = db.session.scalar(
        select(QuizAttempt).where(
            QuizAttempt.student_id == student.id,
            QuizAttempt.module_id == module.id,
            QuizAttempt.status == IN_PROGRESS,
        )
    )
    if attempt is not None:
        _expire_if_late(attempt)


def expire_overdue(user: User, module_id: str) -> None:
    """Chạy trong transaction riêng trước start: start có thể báo lỗi và rollback."""
    student = _student_of(user)
    _expire_open_attempts(student, _module_for(student, module_id))


def start(user: User, module_id: str) -> tuple[dict, int]:
    student = _student_of(user)
    module = _module_for(student, module_id)
    attempts = list(
        db.session.scalars(
            select(QuizAttempt)
            .where(QuizAttempt.student_id == student.id, QuizAttempt.module_id == module.id)
            .order_by(QuizAttempt.attempt_no.desc())
        )
    )
    if any(row.met_threshold for row in attempts):
        raise ApiError(409, "Bạn đã đạt bài kiểm tra này.", "QUIZ_ALREADY_PASSED")
    opened = next((row for row in attempts if row.status == IN_PROGRESS), None)
    if opened is not None:
        return _open_json(opened, module), 200
    now = clock.utcnow()
    if attempts:
        retry_at = _retry_at(attempts[0])
        if now < retry_at:
            raise ApiError(
                409,
                "Chưa đến lúc làm lại bài kiểm tra.",
                "QUIZ_COOLDOWN",
                {"retry_at": iso_time(retry_at)},
            )
    return _create_attempt(student, module, attempts, now), 201


def _create_attempt(
    student: Student, module: CareerModule, attempts: list[QuizAttempt], now: datetime
) -> dict:
    question_ids = list(
        db.session.scalars(
            select(QuizQuestion.id).where(
                QuizQuestion.module_id == module.id, QuizQuestion.status == APPROVED
            )
        )
    )
    count = _config("QUIZ_QUESTION_COUNT")
    if len(question_ids) < count:
        raise ApiError(409, "Mô-đun chưa đủ câu hỏi đã duyệt.", "QUIZ_NOT_READY")
    chosen = _random.sample(question_ids, count)
    options = _options_of(chosen)
    attempt = QuizAttempt(
        student_id=student.id,
        module_id=module.id,
        attempt_no=(attempts[0].attempt_no + 1) if attempts else 1,
        status=IN_PROGRESS,
        started_at=now,
        deadline_at=now + timedelta(minutes=_config("QUIZ_DURATION_MINUTES")),
        total=count,
    )
    db.session.add(attempt)
    try:
        db.session.flush()
    except IntegrityError as error:
        raise ApiError(409, "Bài kiểm tra đã được mở ở nơi khác.", "QUIZ_ALREADY_OPEN") from error
    for order, question_id in enumerate(chosen, start=1):
        ids = [option.id for option in options[question_id]]
        _random.shuffle(ids)
        db.session.add(
            QuizAttemptQuestion(
                attempt_id=attempt.id,
                question_id=question_id,
                order=order,
                option_order=ids,
                selected_option_ids=[],
            )
        )
    db.session.flush()
    return _open_json(attempt, module)


def read_attempt(user: User, attempt_id: str) -> dict:
    attempt = _own_attempt(user, attempt_id)
    _expire_if_late(attempt)
    module = db.session.get(CareerModule, attempt.module_id)
    if attempt.status == IN_PROGRESS:
        return _open_json(attempt, module)
    return _result_json(attempt, module)


def _attempt_closed() -> ApiError:
    return ApiError(409, "Lượt làm bài đã kết thúc.", "ATTEMPT_CLOSED")


def save_answer(user: User, attempt_id: str, question_id: str, option_ids: list[str]) -> dict:
    attempt = _own_attempt(user, attempt_id)
    if attempt.status != IN_PROGRESS or clock.utcnow() >= attempt.deadline_at:
        raise _attempt_closed()
    row = db.session.scalar(
        select(QuizAttemptQuestion).where(
            QuizAttemptQuestion.attempt_id == attempt.id,
            QuizAttemptQuestion.question_id == question_id,
        )
    )
    if row is None:
        raise ApiError(404)
    question = db.session.get(QuizQuestion, question_id)
    chosen = list(dict.fromkeys(option_ids))
    if not set(chosen) <= set(row.option_order):
        raise ApiError(
            422, details={"fields": {"option_ids": ["Lựa chọn không thuộc câu hỏi này."]}}
        )
    if question.kind in SINGLE_ANSWER_KINDS and len(chosen) > 1:
        raise ApiError(422, details={"fields": {"option_ids": ["Câu này chỉ chọn một đáp án."]}})
    row.selected_option_ids = chosen
    return {"question_id": question_id, "selected_option_ids": chosen}


def submit(user: User, attempt_id: str) -> dict:
    """Nộp sau hạn: đóng theo đáp án đã lưu. Nộp lại cùng lượt: 409."""
    attempt = _own_attempt(user, attempt_id)
    now = clock.utcnow()
    late = now >= attempt.deadline_at
    if not _close(attempt, EXPIRED if late else SUBMITTED, attempt.deadline_at if late else now):
        raise _attempt_closed()
    return _result_json(attempt, db.session.get(CareerModule, attempt.module_id))


def review(user: User, module_id: str) -> dict:
    """Ôn tập: các câu đã làm, kèm đáp án và giải thích. Không chấm, không ghi gì."""
    student = _student_of(user)
    module = _module_for(student, module_id)
    closed = list(
        db.session.scalars(
            select(QuizAttempt)
            .where(
                QuizAttempt.student_id == student.id,
                QuizAttempt.module_id == module.id,
                QuizAttempt.status != IN_PROGRESS,
            )
            .order_by(QuizAttempt.attempt_no.desc())
        )
    )
    if not closed:
        raise ApiError(409, "Chưa có lượt làm bài nào để ôn tập.", "NOTHING_TO_REVIEW")
    latest: dict[str, QuizAttemptQuestion] = {}
    for attempt in closed:
        for row in _attempt_rows(attempt):
            latest.setdefault(row.question_id, row)
    return {
        "module": {"id": module.id, "order": module.order, "title": module.title},
        "author_label": AUTHOR_LABEL,
        "questions": _reviewed_questions(list(latest.values())),
    }


def status_by_module(student: Student, modules: list[CareerModule]) -> dict[str, dict]:
    """Trạng thái bài kiểm tra cho khung năng lực. Chỉ đọc, lượt quá hạn được đóng ở lần ghi sau."""
    module_ids = [module.id for module in modules]
    attempts: dict[str, list[QuizAttempt]] = {}
    for row in db.session.scalars(
        select(QuizAttempt)
        .where(QuizAttempt.student_id == student.id, QuizAttempt.module_id.in_(module_ids))
        .order_by(QuizAttempt.attempt_no.desc())
    ):
        attempts.setdefault(row.module_id, []).append(row)
    certificates = {
        row.module_id: row
        for row in db.session.scalars(
            select(Certificate).where(
                Certificate.student_id == student.id, Certificate.module_id.in_(module_ids)
            )
        )
    }
    ready = dict(
        db.session.execute(
            select(QuizQuestion.module_id, func.count())
            .where(QuizQuestion.module_id.in_(module_ids), QuizQuestion.status == APPROVED)
            .group_by(QuizQuestion.module_id)
        ).all()
    )
    now = clock.utcnow()
    found = {}
    for module in modules:
        rows = attempts.get(module.id, [])
        last = rows[0] if rows else None
        state = "not_started"
        retry_at = None
        if any(row.met_threshold for row in rows):
            state = "passed"
        elif last is not None and last.status == IN_PROGRESS and now < last.deadline_at:
            state = "in_progress"
        elif last is not None:
            retry = _retry_at(last)
            state = "cooldown" if now < retry else "retry"
            retry_at = retry if state == "cooldown" else None
        found[module.id] = {
            "state": state,
            "attempt_count": len(rows),
            "open_attempt_id": last.id if state == "in_progress" else None,
            "retry_at": iso_time(retry_at),
            "question_count": ready.get(module.id, 0),
            "can_review": any(row.status != IN_PROGRESS for row in rows),
            "certificate": _certificate_json(certificates[module.id])
            if module.id in certificates
            else None,
        }
    return found


def list_certificates(student: Student) -> dict:
    rows = db.session.scalars(
        select(Certificate)
        .where(Certificate.student_id == student.id)
        .order_by(Certificate.issued_at.desc(), Certificate.code)
    )
    return {"items": [_certificate_json(row) for row in rows], "notice": CERTIFICATE_NOTICE}


def certificate_detail(user: User, code: str) -> dict:
    row = db.session.scalar(select(Certificate).where(Certificate.code == code))
    if row is None or not can_access_student(user, row.student_id):
        raise ApiError(404)
    return _certificate_json(row)


def verify_certificate(code: str) -> dict:
    """Trang công khai: đúng 5 trường, không có mã sinh viên, điểm hay lượt làm bài."""
    row = db.session.scalar(select(Certificate).where(Certificate.code == code))
    if row is None:
        raise ApiError(404)
    return {
        "student_name": row.student_name,
        "module_title": row.module_title,
        "issued_at": iso_time(row.issued_at),
        "valid": row.revoked_at is None,
        "notice": CERTIFICATE_NOTICE,
    }
