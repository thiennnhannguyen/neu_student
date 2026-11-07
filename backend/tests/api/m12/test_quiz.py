"""Bài kiểm tra mô-đun, chứng chỉ, trang xác thực công khai, khung năng lực (CR-04)."""

import json

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.m12 import (
    Certificate,
    QuizAttempt,
    QuizAttemptQuestion,
    QuizOption,
    QuizQuestion,
    SkillEvidence,
)
from app.models.shared import Student
from app.services.quiz_service import CERTIFICATE_NOTICE
from scripts.backend_modules import MODULES
from tests.helpers import FETCH_HEADER as FETCH
from tests.helpers import error_code, login_as

STUDENT = "NEU-KHMT-001"
MODULE_3 = "module-backend-khmt-3"
MODULE_1 = "module-backend-khmt-1"
FRAMEWORK = "/api/m12/careers/slug/backend-developer/framework"
BANNED_WORDS = (
    "tối ưu hóa toàn diện",
    "nâng tầm",
    "trong thời đại số",
    "hành trang",
    "tuyệt vời",
    "xuất sắc",
)


def start(client, module=MODULE_3):
    return client.post(f"/api/m12/modules/{module}/attempts", headers=FETCH)


def answer(client, attempt, question, options):
    return client.put(
        f"/api/m12/attempts/{attempt}/answers/{question}",
        json={"option_ids": options},
        headers=FETCH,
    )


def submit(client, attempt):
    return client.post(f"/api/m12/attempts/{attempt}/submit", headers=FETCH)


def correct_options(app, question_id):
    with app.app_context():
        return list(
            db.session.scalars(
                select(QuizOption.id).where(
                    QuizOption.question_id == question_id, QuizOption.is_correct
                )
            )
        )


def wrong_option(app, question_id):
    with app.app_context():
        return db.session.scalar(
            select(QuizOption.id)
            .where(QuizOption.question_id == question_id, QuizOption.is_correct.is_(False))
            .limit(1)
        )


def fill(app, client, body, wrong=0):
    """Trả lời đúng cả bài, trừ `wrong` câu đầu."""
    for index, question in enumerate(body["questions"]):
        chosen = (
            [wrong_option(app, question["id"])]
            if index < wrong
            else correct_options(app, question["id"])
        )
        assert answer(client, body["id"], question["id"], chosen).status_code == 200


@pytest.fixture
def nhan(demo_app):
    return login_as(demo_app, "thiennhan")


def data_version(app):
    with app.app_context():
        return db.session.get(Student, STUDENT).data_version


# --- Ngân hàng câu hỏi ---


def test_each_module_has_at_least_15_approved_questions_with_explanation():
    assert [m["order"] for m in MODULES] == list(range(1, 11))
    for module in MODULES:
        assert len(module["questions"]) >= 15
        for question in module["questions"]:
            assert question["explanation"]
            assert question["answers"]
            assert question["kind"] in ("single", "multi", "code", "http")
            if question["kind"] != "multi":
                assert len(question["answers"]) == 1, question["prompt"]


def test_question_kinds_cover_all_required_types():
    kinds = {q["kind"] for m in MODULES for q in m["questions"]}
    assert kinds == {"single", "multi", "code", "http"}


def test_writing_rule_has_no_banned_words():
    text = json.dumps(MODULES, ensure_ascii=False).casefold()
    assert [word for word in BANNED_WORDS if word in text] == []


def test_module_courses_have_takeaways_and_exist(demo_app):
    body = login_as(demo_app, "thiennhan").get(FRAMEWORK).get_json()
    assert [module["order"] for module in body["modules"]] == list(range(1, 11))
    for module in body["modules"]:
        assert module["courses"]
        for course in module["courses"]:
            assert course["takeaways"]
            assert course["credits"] > 0
    module_4 = body["modules"][3]
    assert {c["code"] for c in module_4["courses"]} == {"CNTT1107", "CNTT1112", "CNTT1114"}
    assert [c["code"] for c in body["modules"][6]["courses"]] == ["CNTT1117"]


# --- Làm bài ---


def test_start_gives_ten_questions_in_time_without_answers(nhan):
    response = start(nhan)

    assert response.status_code == 201
    body = response.get_json()
    assert len(body["questions"]) == 10
    assert len({q["id"] for q in body["questions"]}) == 10
    assert 14 * 60 < body["remaining_seconds"] <= 15 * 60
    assert body["author_label"] == "Câu hỏi do nhóm biên soạn"
    raw = json.dumps(body)
    assert "is_correct" not in raw
    assert "explanation" not in raw
    for question in body["questions"]:
        assert set(question["options"][0]) == {"id", "text"}


def test_reading_open_attempt_does_not_leak_answers(nhan):
    body = start(nhan).get_json()

    again = nhan.get(f"/api/m12/attempts/{body['id']}").get_json()

    assert "is_correct" not in json.dumps(again)
    assert "explanation" not in json.dumps(again)


def test_start_twice_returns_the_same_attempt(nhan):
    first = start(nhan)
    second = start(nhan)

    assert second.status_code == 200
    assert second.get_json()["id"] == first.get_json()["id"]


def test_two_requests_opening_at_once_lose_with_409(demo_app, nhan, monkeypatch):
    """Request kia đã mở lượt giữa lúc đọc và lúc ghi: chỉ mục unique chặn, không tạo lượt thứ 2."""
    real_flush = db.session.flush
    armed = [True]

    def flush_once(*args, **kwargs):
        if armed[0] and any(isinstance(row, QuizAttempt) for row in db.session.new):
            armed[0] = False
            raise IntegrityError("INSERT", {}, Exception("uq_quiz_attempt_one_open"))
        return real_flush(*args, **kwargs)

    monkeypatch.setattr(db.session, "flush", flush_once, raising=False)

    assert error_code(start(nhan)) == "QUIZ_ALREADY_OPEN"


def test_only_approved_questions_are_used(demo_app, nhan):
    with demo_app.app_context():
        rows = db.session.scalars(
            select(QuizQuestion).where(QuizQuestion.module_id == MODULE_3)
        ).all()
        draft = {row.id for row in rows[:5]}
        for row in rows[:5]:
            row.status = "draft"
        db.session.commit()

    body = start(nhan).get_json()

    assert not {q["id"] for q in body["questions"]} & draft


def test_not_enough_approved_questions_is_409(demo_app, nhan):
    with demo_app.app_context():
        for row in db.session.scalars(
            select(QuizQuestion).where(QuizQuestion.module_id == MODULE_3)
        ).all()[:6]:
            row.status = "draft"
        db.session.commit()

    assert error_code(start(nhan)) == "QUIZ_NOT_READY"


def test_full_marks_pass_with_certificate_evidence_and_data_version(demo_app, nhan):
    body = start(nhan).get_json()
    fill(demo_app, nhan, body)
    version = data_version(demo_app)

    result = submit(nhan, body["id"]).get_json()

    assert result["correct_count"] == 10
    assert result["percent"] == 100
    assert result["passed"] is True
    assert result["certificate"]["student_name"] == "Nguyễn Thiện Nhân"
    assert result["certificate"]["notice"] == CERTIFICATE_NOTICE
    assert data_version(demo_app) == version + 1
    for question in result["questions"]:
        assert question["explanation"]
        assert any(option["is_correct"] for option in question["options"])
    with demo_app.app_context():
        evidence = db.session.scalar(
            select(SkillEvidence).where(
                SkillEvidence.student_id == STUDENT,
                SkillEvidence.skill_id == "sk-backend-khmt-m3",
            )
        )
        assert evidence.status == "approved"
        assert evidence.source == "quiz"


def test_exactly_80_percent_passes(demo_app, nhan):
    body = start(nhan).get_json()
    fill(demo_app, nhan, body, wrong=2)

    result = submit(nhan, body["id"]).get_json()

    assert result["correct_count"] == 8
    assert result["passed"] is True


def test_below_80_percent_fails_without_certificate_or_data_version(demo_app, nhan):
    body = start(nhan).get_json()
    fill(demo_app, nhan, body, wrong=3)
    version = data_version(demo_app)

    result = submit(nhan, body["id"]).get_json()

    assert result["correct_count"] == 7
    assert result["passed"] is False
    assert result["certificate"] is None
    assert result["retry_at"] is not None
    assert data_version(demo_app) == version
    with demo_app.app_context():
        assert (
            db.session.scalar(
                select(Certificate).where(
                    Certificate.student_id == STUDENT, Certificate.module_id == MODULE_3
                )
            )
            is None
        )


def test_multi_answer_needs_the_full_set(demo_app, nhan):
    with demo_app.app_context():
        attempt_kind = {
            row.id for row in db.session.scalars(select(QuizQuestion)) if row.kind == "multi"
        }
    body = start(nhan).get_json()
    multi = next((q for q in body["questions"] if q["id"] in attempt_kind), None)
    while multi is None:  # Lấy ngẫu nhiên: đổi sang câu nhiều đáp án của mô-đun.
        with demo_app.app_context():
            row = db.session.scalars(
                select(QuizAttemptQuestion).where(QuizAttemptQuestion.attempt_id == body["id"])
            ).first()
            question = db.session.scalar(
                select(QuizQuestion).where(
                    QuizQuestion.module_id == MODULE_3, QuizQuestion.kind == "multi"
                )
            )
            row.question_id = question.id
            row.option_order = list(
                db.session.scalars(
                    select(QuizOption.id).where(QuizOption.question_id == question.id)
                )
            )
            db.session.commit()
        body = nhan.get(f"/api/m12/attempts/{body['id']}").get_json()
        multi = next(q for q in body["questions"] if q["id"] in attempt_kind)
    right = correct_options(demo_app, multi["id"])
    fill(demo_app, nhan, body)
    answer(nhan, body["id"], multi["id"], right[:1])

    result = submit(nhan, body["id"]).get_json()

    graded = next(q for q in result["questions"] if q["id"] == multi["id"])
    assert graded["is_correct"] is False
    assert result["correct_count"] == 9


def test_single_answer_question_rejects_two_options(demo_app, nhan):
    body = start(nhan).get_json()
    with demo_app.app_context():
        kinds = dict(db.session.execute(select(QuizQuestion.id, QuizQuestion.kind)).all())
    single = next(q for q in body["questions"] if kinds[q["id"]] != "multi")
    ids = [option["id"] for option in single["options"]][:2]

    assert answer(nhan, body["id"], single["id"], ids).status_code == 422


def test_option_of_other_question_is_422(nhan):
    body = start(nhan).get_json()
    first, second = body["questions"][:2]

    response = answer(nhan, body["id"], first["id"], [second["options"][0]["id"]])

    assert response.status_code == 422


def test_unknown_question_is_404_and_missing_field_is_422(nhan):
    body = start(nhan).get_json()

    assert answer(nhan, body["id"], "khong-co", []).status_code == 404
    response = nhan.put(
        f"/api/m12/attempts/{body['id']}/answers/{body['questions'][0]['id']}",
        json={},
        headers=FETCH,
    )
    assert response.status_code == 422


def test_submit_twice_is_409_and_grades_once(demo_app, nhan):
    body = start(nhan).get_json()
    fill(demo_app, nhan, body)
    assert submit(nhan, body["id"]).status_code == 200

    second = submit(nhan, body["id"])

    assert second.status_code == 409
    assert error_code(second) == "ATTEMPT_CLOSED"
    with demo_app.app_context():
        assert (
            len(
                db.session.scalars(
                    select(Certificate).where(
                        Certificate.student_id == STUDENT, Certificate.module_id == MODULE_3
                    )
                ).all()
            )
            == 1
        )


def test_answer_after_submit_is_409(demo_app, nhan):
    body = start(nhan).get_json()
    submit(nhan, body["id"])

    response = answer(nhan, body["id"], body["questions"][0]["id"], [])

    assert error_code(response) == "ATTEMPT_CLOSED"


def test_late_read_auto_submits_saved_answers(demo_app, nhan, fake_clock):
    body = start(nhan).get_json()
    fill(demo_app, nhan, body)
    fake_clock.advance(minutes=16)

    result = nhan.get(f"/api/m12/attempts/{body['id']}").get_json()

    assert result["status"] == "expired"
    assert result["auto_submitted"] is True
    assert result["correct_count"] == 10
    assert result["passed"] is True


def test_answer_after_deadline_is_rejected_and_late_submit_uses_saved(demo_app, nhan, fake_clock):
    body = start(nhan).get_json()
    fake_clock.advance(minutes=15)
    question = body["questions"][0]

    response = answer(nhan, body["id"], question["id"], correct_options(demo_app, question["id"]))
    assert error_code(response) == "ATTEMPT_CLOSED"

    result = submit(nhan, body["id"]).get_json()
    assert result["status"] == "expired"
    assert result["correct_count"] == 0


def test_expired_open_attempt_is_closed_when_starting_again(demo_app, nhan, fake_clock):
    body = start(nhan).get_json()
    fake_clock.advance(minutes=16)

    response = start(nhan)

    assert error_code(response) == "QUIZ_COOLDOWN"
    with demo_app.app_context():
        assert db.session.get(QuizAttempt, body["id"]).status == "expired"


def test_cooldown_of_expired_attempt_counts_from_the_deadline(nhan, fake_clock):
    start(nhan)
    fake_clock.advance(minutes=24)
    assert error_code(start(nhan)) == "QUIZ_COOLDOWN"

    fake_clock.advance(minutes=1)

    assert start(nhan).status_code == 201


def test_cooldown_blocks_until_it_ends_and_all_attempts_are_kept(demo_app, nhan, fake_clock):
    body = start(nhan).get_json()
    submit(nhan, body["id"])

    blocked = start(nhan)
    assert blocked.status_code == 409
    assert error_code(blocked) == "QUIZ_COOLDOWN"
    assert blocked.get_json()["error"]["details"]["retry_at"]

    fake_clock.advance(minutes=9)
    assert error_code(start(nhan)) == "QUIZ_COOLDOWN"

    fake_clock.advance(minutes=1)
    again = start(nhan)
    assert again.status_code == 201
    assert again.get_json()["attempt_no"] == 2
    with demo_app.app_context():
        rows = db.session.scalars(
            select(QuizAttempt).where(
                QuizAttempt.student_id == STUDENT, QuizAttempt.module_id == MODULE_3
            )
        ).all()
        assert len(rows) == 2


def test_cooldown_is_configurable(demo_app, nhan, fake_clock):
    demo_app.config["QUIZ_RETRY_COOLDOWN_MINUTES"] = 1
    body = start(nhan).get_json()
    submit(nhan, body["id"])

    fake_clock.advance(minutes=1)

    assert start(nhan).status_code == 201


def test_passed_module_cannot_be_retaken_but_can_be_reviewed(nhan):
    assert error_code(start(nhan, MODULE_1)) == "QUIZ_ALREADY_PASSED"

    review = nhan.get(f"/api/m12/modules/{MODULE_1}/review")

    assert review.status_code == 200
    questions = review.get_json()["questions"]
    assert len(questions) == 10
    assert all(q["explanation"] for q in questions)


def test_review_writes_nothing(demo_app, nhan):
    def rows():
        with demo_app.app_context():
            return (
                len(db.session.scalars(select(QuizAttempt)).all()),
                data_version(demo_app),
            )

    before = rows()
    nhan.get(f"/api/m12/modules/{MODULE_1}/review")

    assert rows() == before


def test_review_before_any_attempt_is_409(nhan):
    assert error_code(nhan.get(f"/api/m12/modules/{MODULE_3}/review")) == "NOTHING_TO_REVIEW"


# --- Quyền ---


def test_other_student_cannot_touch_the_attempt(demo_app, nhan):
    body = start(nhan).get_json()
    other = login_as(demo_app, "demo05")

    assert other.get(f"/api/m12/attempts/{body['id']}").status_code == 404
    assert submit(other, body["id"]).status_code == 404


def test_student_of_other_program_has_no_module(demo_app):
    client = login_as(demo_app, "demo01")

    assert start(client).status_code == 404


def test_khmt_student_without_attempts_can_start(demo_app):
    assert start(login_as(demo_app, "demo05")).status_code == 201


@pytest.mark.parametrize("username", ["gv2", "admin", "ht1"])
def test_only_students_can_start(demo_app, username):
    assert start(login_as(demo_app, username)).status_code == 403


def test_anonymous_gets_401(demo_app):
    assert start(demo_app.test_client()).status_code == 401


def test_missing_module_is_404(nhan):
    assert start(nhan, "khong-co").status_code == 404


def test_write_without_csrf_header_is_rejected(nhan):
    response = nhan.post(f"/api/m12/modules/{MODULE_3}/attempts")

    assert response.status_code == 403


# --- Chứng chỉ ---


def certificate_code(demo_app):
    with demo_app.app_context():
        return db.session.scalar(select(Certificate.code).where(Certificate.module_id == MODULE_1))


def test_seed_gives_two_certificates(nhan):
    body = nhan.get("/api/m12/certificates").get_json()

    assert [item["module_title"] for item in body["items"]] == [
        "Ngôn ngữ backend và OOP",
        "Nền tảng lập trình và thuật toán",
    ]
    assert body["notice"] == CERTIFICATE_NOTICE
    assert all(item["correct_count"] == 9 for item in body["items"])


def test_public_verification_shows_only_the_allowed_fields(demo_app):
    response = demo_app.test_client().get(f"/api/public/certificates/{certificate_code(demo_app)}")

    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == {"student_name", "module_title", "issued_at", "valid", "notice"}
    assert body["student_name"] == "Nguyễn Thiện Nhân"
    assert body["valid"] is True
    assert body["notice"] == CERTIFICATE_NOTICE
    raw = json.dumps(body)
    assert STUDENT not in raw
    assert "correct_count" not in raw
    assert "email" not in raw


def test_wrong_verification_code_is_404(demo_app):
    assert demo_app.test_client().get("/api/public/certificates/khong-co").status_code == 404


def test_revoked_certificate_is_not_valid(demo_app):
    code = certificate_code(demo_app)
    with demo_app.app_context():
        row = db.session.scalar(select(Certificate).where(Certificate.code == code))
        row.revoked_at = row.issued_at
        db.session.commit()

    assert (
        demo_app.test_client().get(f"/api/public/certificates/{code}").get_json()["valid"] is False
    )


def test_new_certificate_code_is_long_and_unguessable(demo_app, nhan):
    body = start(nhan).get_json()
    fill(demo_app, nhan, body)

    code = submit(nhan, body["id"]).get_json()["certificate"]["code"]

    assert len(code) >= 24
    assert STUDENT not in code


def test_certificate_detail_permissions(demo_app):
    code = certificate_code(demo_app)

    assert login_as(demo_app, "thiennhan").get(f"/api/m12/certificates/{code}").status_code == 200
    assert login_as(demo_app, "gv2").get(f"/api/m12/certificates/{code}").status_code == 200
    assert login_as(demo_app, "gv1").get(f"/api/m12/certificates/{code}").status_code == 404
    assert login_as(demo_app, "demo05").get(f"/api/m12/certificates/{code}").status_code == 404


# --- Tiến độ và khung năng lực ---


def skill_progress(client):
    body = client.get("/api/m12/progress/careers/slug/backend-developer").get_json()
    return body["skill_progress"]["numerator"], body["skill_progress"]["denominator"]


def test_backend_denominator_is_13_for_khmt_and_9_for_other_program(demo_app):
    assert skill_progress(login_as(demo_app, "thiennhan"))[1] == 13
    assert skill_progress(login_as(demo_app, "demo05"))[1] == 13
    assert skill_progress(login_as(demo_app, "demo01"))[1] == 9


def test_passing_quiz_raises_skill_progress_on_the_career(demo_app, nhan):
    before = skill_progress(nhan)
    assert before == (2, 13)
    body = start(nhan).get_json()
    fill(demo_app, nhan, body)

    submit(nhan, body["id"])

    assert skill_progress(nhan) == (3, 13)


def test_module_skill_cannot_get_a_manual_evidence(nhan):
    response = nhan.post(
        "/api/m12/evidences",
        data={"skill_id": "sk-backend-khmt-m3", "description": "Nộp tay"},
        headers=FETCH,
    )

    assert response.status_code == 422
    assert error_code(response) == "SKILL_NEEDS_QUIZ"


def test_framework_status_of_seeded_student(nhan):
    body = nhan.get(FRAMEWORK).get_json()

    states = [module["quiz"]["state"] for module in body["modules"]]
    assert states[:3] == ["passed", "passed", "not_started"]
    assert body["modules"][0]["quiz"]["certificate"]["code"]
    assert body["modules"][0]["skill_done"] is True
    assert body["source"] == "Nhóm biên soạn"
    names = [row["name"] for row in body["milestones"]]
    assert names == ["Thực tập sinh", "Fresher", "Junior"]
    assert body["milestones"][0]["modules_done"] == 2


def test_framework_quiz_states_follow_attempts(demo_app, nhan, fake_clock):
    body = start(nhan).get_json()
    state = lambda: nhan.get(FRAMEWORK).get_json()["modules"][2]["quiz"]  # noqa: E731
    assert state()["state"] == "in_progress"
    assert state()["open_attempt_id"] == body["id"]

    # Hết giờ lúc 15 phút, chờ 10 phút tính từ lúc đó, kể cả khi chưa ai đóng lượt.
    fake_clock.advance(minutes=16)
    assert state()["state"] == "cooldown"

    nhan.get(f"/api/m12/attempts/{body['id']}")
    assert state()["state"] == "cooldown"
    assert state()["can_review"] is True

    fake_clock.advance(minutes=9)
    assert state()["state"] == "retry"


def test_framework_cooldown_state(demo_app, nhan):
    body = start(nhan).get_json()
    submit(nhan, body["id"])

    quiz = nhan.get(FRAMEWORK).get_json()["modules"][2]["quiz"]

    assert quiz["state"] == "cooldown"
    assert quiz["retry_at"]


def test_framework_electives_and_replacement(nhan):
    electives = nhan.get(FRAMEWORK).get_json()["electives"]

    assert len(electives["suggested"]) == 10
    assert electives["allocation"]["curriculum"] == {"4": 6, "5": 6, "6": 9, "7": 9}
    assert electives["allocation"]["suggested"] == {"4": 9, "5": 9, "6": 6, "7": 6}
    assert electives["replaced"] == []


def test_framework_shows_replacement_when_student_chose_other_elective(demo_app):
    client = login_as(demo_app, "demo05")
    with demo_app.app_context():
        from app.models.shared import Enrollment

        db.session.add(
            Enrollment(
                id="enr-x",
                student_id="DEMO05",
                course_id="CNTT1174",
                semester_id="S5",
                status="in_progress",
            )
        )
        db.session.commit()

    replaced = client.get(FRAMEWORK).get_json()["electives"]["replaced"]

    assert replaced[0]["chosen"]["code"] == "CNTT1174"
    assert replaced[0]["instead_of"]["code"]


def test_framework_is_empty_for_other_programs_and_other_careers(demo_app):
    assert login_as(demo_app, "demo01").get(FRAMEWORK).get_json()["modules"] == []
    other = login_as(demo_app, "thiennhan").get("/api/m12/careers/slug/ai-engineer/framework")
    assert other.get_json()["modules"] == []
    assert (
        login_as(demo_app, "thiennhan").get("/api/m12/careers/slug/khong-co/framework").status_code
        == 404
    )


def test_advisor_reads_framework_of_own_student_only(demo_app):
    query = f"{FRAMEWORK}?student_id={STUDENT}"

    assert login_as(demo_app, "gv2").get(query).status_code == 200
    assert login_as(demo_app, "gv1").get(query).status_code == 404
