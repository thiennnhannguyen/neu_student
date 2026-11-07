"""Thông báo: chỉ của mình, đọc, đọc tất cả, chống trùng, thông báo lộ trình (Q106)."""

from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from app.common import clock
from app.extensions import db
from app.models.system import Notification
from app.services import grades_service, notification_service, roadmap_api_service
from tests.api.m11.helpers import QueryCounter
from tests.helpers import FETCH_HEADER, login_as

URL = "/api/notifications"
NOTE = "Thông báo lộ trình cập nhật khi bạn mở ứng dụng."
QUERIES_LIST_NO_ROADMAP = 9


def add(app, user_id="user-sv04", key="k1", title="Tiêu đề"):
    with app.app_context():
        notification_service.notify(user_id, "ticket_update", title, None, "/x", key)
        db.session.commit()


def count(app, user_id="user-sv04"):
    with app.app_context():
        return db.session.scalar(
            select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
        )


def post(client, url):
    return client.post(url, json={}, headers=FETCH_HEADER)


def test_anonymous_gets_401(http_app):
    assert http_app.test_client().get(URL).status_code == 401


def test_same_event_twice_gives_one_notification(http_app):
    add(http_app)
    add(http_app)

    assert count(http_app) == 1


def test_same_key_for_other_user_is_separate(http_app):
    add(http_app)
    add(http_app, "user-sv01")

    assert count(http_app) == 1
    assert count(http_app, "user-sv01") == 1


def test_list_has_unread_count_newest_first_and_note(http_app):
    add(http_app, key="a", title="Cũ")
    add(http_app, key="b", title="Mới")

    body = login_as(http_app, "sv04").get(URL).get_json()

    assert body["unread_count"] == 2
    assert body["total"] == 2
    assert [row["title"] for row in body["items"]] == ["Mới", "Cũ"]
    assert body["items"][0]["read"] is False
    assert body["note"] == NOTE


def test_only_own_notifications(http_app):
    add(http_app)

    assert login_as(http_app, "sv01").get(URL).get_json()["items"] == []


def test_read_one_and_twice(http_app):
    add(http_app)
    client = login_as(http_app, "sv04")
    row = client.get(URL).get_json()["items"][0]

    first = post(client, f"{URL}/{row['id']}/read")
    assert first.status_code == 200
    assert first.get_json()["unread_count"] == 0
    assert post(client, f"{URL}/{row['id']}/read").status_code == 200
    assert client.get(URL).get_json()["items"][0]["read"] is True


def test_cannot_read_notification_of_other_user(http_app):
    add(http_app)
    row = login_as(http_app, "sv04").get(URL).get_json()["items"][0]

    assert post(login_as(http_app, "sv01"), f"{URL}/{row['id']}/read").status_code == 404
    assert post(login_as(http_app, "sv04"), f"{URL}/99999/read").status_code == 404


def test_read_all_only_touches_own(http_app):
    add(http_app, key="a")
    add(http_app, key="b")
    add(http_app, "user-sv01", key="c")
    client = login_as(http_app, "sv04")

    assert post(client, f"{URL}/read-all").get_json() == {"unread_count": 0}
    assert client.get(URL).get_json()["unread_count"] == 0
    assert login_as(http_app, "sv01").get(URL).get_json()["unread_count"] == 1


def test_every_role_can_read(http_app):
    for username in ("gv1", "admin", "ht1", "sv01"):
        assert login_as(http_app, username).get(URL).status_code == 200


def test_page_size_is_validated(http_app):
    assert login_as(http_app, "sv01").get(f"{URL}?page=x").status_code == 422


def proposal_notices(app, user_id="user-sv07"):
    with app.app_context():
        return db.session.scalars(
            select(Notification).where(
                Notification.user_id == user_id, Notification.kind == "roadmap_proposal"
            )
        ).all()


def failing_course(roadmap):
    item = next(
        item
        for column in roadmap["semesters"]
        for item in column["items"]
        if item["depends_on_pending_result"]
    )
    return next(p["course_id"] for p in item["prerequisites"] if p["status"] == "in_progress")


def fail(app, course):
    with app.app_context():
        grades_service.add_grade_result("SV07", course, "S5", "2.0")
        db.session.commit()


def test_proposal_notification_is_created_on_read_once(http_app):
    client = login_as(http_app, "sv07")
    roadmap = post(client, "/api/m12/roadmaps/generate").get_json()["roadmap"]

    client.get(URL)
    assert proposal_notices(http_app) == []

    fail(http_app, failing_course(roadmap))
    client.get(URL)
    client.get(URL)

    notices = proposal_notices(http_app)
    assert len(notices) == 1
    assert notices[0].link == "/m12/ke-hoach/khac-biet"


def test_no_notification_for_student_without_roadmap_or_primary(http_app):
    login_as(http_app, "sv05").get(URL)

    assert proposal_notices(http_app, "user-sv05") == []


def test_no_notification_when_primary_career_is_gone(http_app):
    from app.models.m12 import StudentCareerGoal

    client = login_as(http_app, "sv07")
    post(client, "/api/m12/roadmaps/generate")
    with http_app.app_context():
        goal = db.session.scalar(
            select(StudentCareerGoal).where(
                StudentCareerGoal.student_id == "SV07", StudentCareerGoal.ended_at.is_(None)
            )
        )
        goal.ended_at = clock.utcnow()
        db.session.commit()

    assert client.get(URL).status_code == 200
    assert proposal_notices(http_app) == []


def test_no_notification_after_dismiss(http_app):
    client = login_as(http_app, "sv07")
    roadmap = post(client, "/api/m12/roadmaps/generate").get_json()["roadmap"]
    fail(http_app, failing_course(roadmap))
    url = f"/api/m12/roadmaps/{roadmap['id']}/proposal"
    stamp = client.get(url).get_json()["stamp"]
    client.post(f"{url}/dismiss", json={"stamp": stamp}, headers=FETCH_HEADER)

    client.get(URL)

    assert proposal_notices(http_app) == []


def test_stale_without_plan_change_gives_no_notification_and_computes_once(http_app, monkeypatch):
    from app.common.data_version import bump_data_version
    from app.models.shared import Student

    client = login_as(http_app, "sv07")
    post(client, "/api/m12/roadmaps/generate")
    with http_app.app_context():
        bump_data_version(db.session.get(Student, "SV07"))
        db.session.commit()
    calls = []
    real = roadmap_api_service._proposal

    def counted(*args):
        calls.append(1)
        return real(*args)

    monkeypatch.setattr(roadmap_api_service, "_proposal", counted)
    client.get(URL)
    client.get(URL)

    assert proposal_notices(http_app) == []
    assert len(calls) == 1


def test_locked_database_does_not_break_the_list_and_next_read_creates_notice(
    http_app, monkeypatch
):
    client = login_as(http_app, "sv07")
    roadmap = post(client, "/api/m12/roadmaps/generate").get_json()["roadmap"]
    fail(http_app, failing_course(roadmap))

    def locked(*_args, **_kwargs):
        raise OperationalError("INSERT", {}, Exception("database is locked"))

    with monkeypatch.context() as patch:
        patch.setattr(roadmap_api_service, "notify", locked)
        response = client.get(URL)
        assert response.status_code == 200
        assert response.get_json()["items"] == []
    assert proposal_notices(http_app) == []

    assert client.get(URL).status_code == 200
    assert len(proposal_notices(http_app)) == 1


def test_existing_notice_is_not_written_again(http_app, monkeypatch):
    client = login_as(http_app, "sv07")
    roadmap = post(client, "/api/m12/roadmaps/generate").get_json()["roadmap"]
    fail(http_app, failing_course(roadmap))
    client.get(URL)
    assert len(proposal_notices(http_app)) == 1

    def must_not_write(*_args, **_kwargs):
        raise AssertionError("Không được ghi lại")

    monkeypatch.setattr(roadmap_api_service, "notify", must_not_write)
    assert client.get(URL).status_code == 200


def test_query_count_without_roadmap_is_fixed(http_app):
    client = login_as(http_app, "sv01")

    with QueryCounter(http_app) as counter:
        assert client.get(URL).status_code == 200

    assert counter.count == QUERIES_LIST_NO_ROADMAP


def test_query_counts_with_roadmap(http_app):
    client = login_as(http_app, "sv07")
    roadmap = post(client, "/api/m12/roadmaps/generate").get_json()["roadmap"]
    with QueryCounter(http_app) as fresh:
        assert client.get(URL).status_code == 200

    fail(http_app, failing_course(roadmap))
    with QueryCounter(http_app) as stale:
        assert client.get(URL).status_code == 200
    with QueryCounter(http_app) as again:
        assert client.get(URL).status_code == 200

    assert fresh.count == 13
    assert stale.count == 61
    assert again.count == 14
