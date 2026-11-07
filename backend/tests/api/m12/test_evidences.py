"""Minh chứng: nộp, duyệt, từ chối, % trên mọi nghề, data_version, thông báo, tệp, quyền."""

import io

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.m12 import SkillEvidence, SkillEvidenceAttachment
from app.models.shared import Student
from app.models.system import AuditLog, Notification
from tests.api.m11.helpers import QueryCounter
from tests.helpers import FETCH_HEADER, error_code, login_as

PDF = b"%PDF-1.7 mau"
EVIDENCES = "/api/m12/evidences"
REVIEWS = "/api/m12/evidence-reviews"
QUERIES_REVIEW_LIST = 7


def submit(client, skill_id="sk-git", files=(), **extra):
    data = {"skill_id": skill_id, "description": "Kho mã nhóm", **extra}
    if files:
        data["files"] = [(io.BytesIO(content), name) for name, content in files]
    return client.post(
        EVIDENCES, data=data, headers=FETCH_HEADER, content_type="multipart/form-data"
    )


def review(client, evidence_id, action, note=None):
    body = {} if note is None else {"note": note}
    return client.post(f"{REVIEWS}/{evidence_id}/{action}", json=body, headers=FETCH_HEADER)


def data_version(app, student_id):
    with app.app_context():
        return db.session.get(Student, student_id).data_version


def percents(client):
    body = client.get("/api/m12/gallery").get_json()
    return {i["career"]["id"]: i["skill_progress"]["numerator"] for i in body["items"]}


def rows(app, model):
    with app.app_context():
        return db.session.scalars(select(model)).all()


def test_submit_returns_pending_and_bumps_data_version(http_app):
    client = login_as(http_app, "sv04")
    before = data_version(http_app, "SV04")

    response = submit(client, link="https://example.test/kho")
    body = response.get_json()

    assert response.status_code == 201
    assert body["status"] == "pending"
    assert body["skill"]["id"] == "sk-git"
    assert body["link"] == "https://example.test/kho"
    assert data_version(http_app, "SV04") == before + 1


@pytest.mark.parametrize(
    ("extra", "field"),
    [
        ({"description": ""}, "description"),
        ({"description": "x" * 1001}, "description"),
        ({"link": "ftp://example.test/a"}, "link"),
        ({"link": "javascript:alert(1)"}, "link"),
        ({"link": "https://example.test/" + "a" * 600}, "link"),
    ],
)
def test_submit_validates_fields(http_app, extra, field):
    response = submit(login_as(http_app, "sv04"), **extra)

    assert response.status_code == 422
    assert field in response.get_json()["error"]["details"]["fields"]


def test_description_of_exactly_1000_is_allowed(http_app):
    assert submit(login_as(http_app, "sv04"), description="x" * 1000).status_code == 201


def test_skill_not_in_any_career_is_422(http_app):
    with http_app.app_context():
        from tests.helpers import run_sql

        run_sql(
            "INSERT INTO skills (id, name, kind, name_key, is_mock) "
            "VALUES ('sk-tam', 'Tạm', 'skill', 'tam', 1)"
        )
        db.session.commit()

    assert submit(login_as(http_app, "sv04"), "sk-tam").status_code == 422


def test_empty_link_from_form_counts_as_no_link(http_app):
    response = submit(login_as(http_app, "sv04"), link="")

    assert response.status_code == 201
    assert response.get_json()["link"] is None


def test_pending_or_approved_blocks_new_submission_rejected_allows_it(http_app):
    client = login_as(http_app, "sv04")
    first = submit(client).get_json()

    assert submit(client).status_code == 409
    advisor = login_as(http_app, advisor_of(http_app, "SV04"))
    assert review(advisor, first["id"], "reject", "Thiếu liên kết").status_code == 200

    second = submit(client)
    assert second.status_code == 201
    history = client.get(f"{EVIDENCES}?skill_id=sk-git").get_json()["items"]
    assert {row["status"] for row in history} == {"pending", "rejected"}
    assert len(history) == 2
    assert review(advisor, second.get_json()["id"], "approve").status_code == 200
    assert submit(client).status_code == 409


def advisor_of(app, student_id):
    with app.app_context():
        from app.models.shared import AdvisorAssignment, User

        return db.session.scalar(
            select(User.username)
            .join(AdvisorAssignment, AdvisorAssignment.advisor_user_id == User.id)
            .where(AdvisorAssignment.student_id == student_id)
        )


def test_only_student_can_submit(http_app):
    for username in ("gv1", "admin", "ht1"):
        assert submit(login_as(http_app, username)).status_code == 403


def test_too_many_files_is_422(http_app):
    files = [(f"{n}.pdf", PDF) for n in range(3)]

    response = submit(login_as(http_app, "sv04"), files=files)

    assert response.status_code == 422
    assert error_code(response) == "ATTACHMENT_INVALID"


def test_exe_renamed_pdf_and_6mb_are_rejected_and_nothing_saved(http_app):
    client = login_as(http_app, "sv04")
    before = len(rows(http_app, SkillEvidence))

    fake = submit(client, files=[("virus.pdf", b"MZ\x90\x00")])
    big = submit(client, files=[("lon.pdf", PDF + b"x" * (6 * 1024 * 1024))])

    assert fake.status_code == 422
    assert big.status_code == 422
    assert len(rows(http_app, SkillEvidence)) == before


def test_request_above_limit_is_413(http_app):
    response = submit(
        login_as(http_app, "sv04"), files=[("a.pdf", PDF + b"x" * (17 * 1024 * 1024))]
    )

    assert response.status_code == 413


def test_attachment_download_scope(http_app):
    owner = login_as(http_app, "sv04")
    body = submit(owner, files=[("bai lam.pdf", PDF)]).get_json()
    url = body["attachments"][0]["url"]

    response = owner.get(url)
    assert response.status_code == 200
    assert response.data == PDF
    assert "attachment" in response.headers["Content-Disposition"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert login_as(http_app, advisor_of(http_app, "SV04")).get(url).status_code == 200
    assert login_as(http_app, "admin").get(url).status_code == 200
    assert login_as(http_app, "sv01").get(url).status_code == 404
    assert login_as(http_app, "ht1").get(url).status_code == 404
    other = "gv1" if advisor_of(http_app, "SV04") == "gv2" else "gv2"
    assert login_as(http_app, other).get(url).status_code == 404
    with http_app.app_context():
        stored = db.session.scalar(select(SkillEvidenceAttachment))
        assert stored.original_name == "bai lam.pdf"
        assert stored.stored_name != "bai lam.pdf"
        assert len(stored.sha256) == 64


def test_attachment_of_other_evidence_or_unknown_is_404(http_app):
    owner = login_as(http_app, "sv04")
    body = submit(owner, files=[("a.pdf", PDF)]).get_json()
    other = submit(owner, "sk-sql").get_json()
    attachment = body["attachments"][0]["id"]

    assert owner.get(f"{EVIDENCES}/{other['id']}/attachments/{attachment}").status_code == 404
    assert owner.get(f"{EVIDENCES}/{body['id']}/attachments/khong").status_code == 404
    assert owner.get(f"{EVIDENCES}/khong/attachments/{attachment}").status_code == 404


def test_approving_git_changes_every_career_with_git_only(http_app):
    student = login_as(http_app, "sv04")
    before = percents(student)
    body = submit(student).get_json()
    version = data_version(http_app, "SV04")

    response = review(login_as(http_app, advisor_of(http_app, "SV04")), body["id"], "approve")

    assert response.status_code == 200
    assert response.get_json()["status"] == "approved"
    assert data_version(http_app, "SV04") == version + 1
    after = percents(student)
    changed = {career for career in after if after[career] != before[career]}
    assert len(changed) >= 2
    assert all(after[career] == before[career] + 1 for career in changed)
    with http_app.app_context():
        from app.models.m12 import CareerRequirement, CareerVersion

        with_git = set(
            db.session.scalars(
                select(CareerVersion.career_id)
                .join(CareerRequirement, CareerRequirement.career_version_id == CareerVersion.id)
                .where(CareerRequirement.skill_id == "sk-git", CareerVersion.status == "published")
            )
        )
    assert changed == with_git


def test_review_writes_audit_and_notification(http_app):
    student = login_as(http_app, "sv04")
    evidence = submit(student).get_json()["id"]

    review(login_as(http_app, advisor_of(http_app, "SV04")), evidence, "reject", "Thiếu liên kết")

    with http_app.app_context():
        actions = db.session.scalars(
            select(AuditLog.action).where(AuditLog.entity_id == evidence)
        ).all()
        notice = db.session.scalar(
            select(Notification).where(Notification.kind == "evidence_review")
        )
        assert set(actions) == {"evidence.submit", "evidence.reject"}
        assert "bị từ chối" in notice.title
        assert notice.body == "Thiếu liên kết"
        assert notice.user_id == "user-sv04"


@pytest.mark.parametrize("body", [{}, {"note": ""}, {"note": "   "}])
def test_reject_without_reason_is_422_and_db_unchanged(http_app, body):
    student = login_as(http_app, "sv04")
    evidence = submit(student).get_json()["id"]
    version = data_version(http_app, "SV04")
    advisor = login_as(http_app, advisor_of(http_app, "SV04"))

    response = advisor.post(f"{REVIEWS}/{evidence}/reject", json=body, headers=FETCH_HEADER)

    assert response.status_code == 422
    assert data_version(http_app, "SV04") == version
    with http_app.app_context():
        assert db.session.get(SkillEvidence, evidence).status == "pending"


def test_review_twice_is_409(http_app):
    evidence = submit(login_as(http_app, "sv04")).get_json()["id"]
    advisor = login_as(http_app, advisor_of(http_app, "SV04"))

    assert review(advisor, evidence, "approve", "Tốt").status_code == 200
    second = review(advisor, evidence, "reject", "Đổi ý")
    assert second.status_code == 409
    assert error_code(second) == "EVIDENCE_REVIEWED"


def test_review_scope_and_roles(http_app):
    evidence = submit(login_as(http_app, "sv04")).get_json()["id"]
    assigned = advisor_of(http_app, "SV04")
    other = login_as(http_app, "gv1" if assigned == "gv2" else "gv2")

    assert review(other, evidence, "approve").status_code == 404
    assert other.get(f"{REVIEWS}/{evidence}").status_code == 404
    assert review(login_as(http_app, "admin"), evidence, "approve").status_code == 403
    assert review(login_as(http_app, "sv04"), evidence, "approve").status_code == 403
    assert login_as(http_app, "sv04").get(REVIEWS).status_code == 403
    assert login_as(http_app, "ht1").get(REVIEWS).status_code == 403
    assert review(login_as(http_app, assigned), "khong-co", "approve").status_code == 404


def test_review_queue_filters_and_scope(http_app):
    evidence = submit(login_as(http_app, "sv04")).get_json()["id"]
    assigned = advisor_of(http_app, "SV04")

    body = login_as(http_app, assigned).get(f"{REVIEWS}?status=pending").get_json()
    ids = {row["id"] for row in body["items"]}
    assert evidence in ids
    row = next(row for row in body["items"] if row["id"] == evidence)
    assert row["student"]["code"] == "SV04"

    other = "gv1" if assigned == "gv2" else "gv2"
    assert evidence not in {
        r["id"] for r in login_as(http_app, other).get(REVIEWS).get_json()["items"]
    }
    admin = login_as(http_app, "admin").get(REVIEWS).get_json()
    assert evidence in {r["id"] for r in admin["items"]}
    assert login_as(http_app, "admin").get(f"{REVIEWS}/{evidence}").status_code == 200
    approved = login_as(http_app, "admin").get(f"{REVIEWS}?status=approved").get_json()
    assert all(r["status"] == "approved" for r in approved["items"])
    assert login_as(http_app, assigned).get(f"{REVIEWS}?status=sai").status_code == 422


def test_advisor_reads_student_history_only_when_assigned(http_app):
    assigned = advisor_of(http_app, "SV04")
    other = "gv1" if assigned == "gv2" else "gv2"

    assert login_as(http_app, assigned).get(f"{EVIDENCES}?student_id=SV04").status_code == 200
    assert login_as(http_app, other).get(f"{EVIDENCES}?student_id=SV04").status_code == 404


def test_approving_may_create_proposal_only_if_plan_changes(http_app):
    """Kỹ năng đã duyệt biến mất khỏi gợi ý nên kết quả xếp đổi và có đề xuất."""
    student = login_as(http_app, "sv04")
    roadmap = student.post("/api/m12/roadmaps/generate", json={}, headers=FETCH_HEADER).get_json()[
        "roadmap"
    ]
    assert "sk-git" in {s["skill"]["id"] for c in roadmap["semesters"] for s in c["skills"]}
    evidence = submit(student).get_json()["id"]
    assert student.get("/api/m12/roadmaps/current").get_json()["roadmap"]["has_proposal"] is False

    review(login_as(http_app, advisor_of(http_app, "SV04")), evidence, "approve")

    current = student.get("/api/m12/roadmaps/current").get_json()["roadmap"]
    assert current["stale"] is True
    assert current["has_proposal"] is True


def test_demo05_checklist_skill(demo_app):
    """Cẩm nang không có kỹ năng dùng chung: % chỉ đổi đúng nghề chứa kỹ năng đó (Q103)."""
    student = login_as(demo_app, "demo05")
    before = percents(student)
    version = data_version(demo_app, "DEMO05")
    pending = student.get(f"{EVIDENCES}?skill_id=sk-k68-ai-2").get_json()["items"][0]

    response = review(login_as(demo_app, "gv2"), pending["id"], "approve")

    assert response.status_code == 200
    after = percents(student)
    assert {c for c in after if after[c] != before[c]} == {"career-k68-ai"}
    assert after["career-k68-ai"] == before["career-k68-ai"] + 1
    assert data_version(demo_app, "DEMO05") == version + 1


def test_query_count_of_review_list(http_app):
    submit(login_as(http_app, "sv04"))
    advisor = login_as(http_app, advisor_of(http_app, "SV04"))
    with QueryCounter(http_app) as counter:
        assert advisor.get(REVIEWS).status_code == 200

    assert counter.count == QUERIES_REVIEW_LIST


def test_query_counts_of_student_list_and_review_detail(http_app):
    student = login_as(http_app, "sv04")
    evidence = submit(student, files=[("a.pdf", PDF)]).get_json()["id"]
    advisor = login_as(http_app, advisor_of(http_app, "SV04"))

    with QueryCounter(http_app) as listed:
        assert student.get(EVIDENCES).status_code == 200
    with QueryCounter(http_app) as detail:
        assert advisor.get(f"{REVIEWS}/{evidence}").status_code == 200

    assert listed.count == 7
    assert detail.count == 9
