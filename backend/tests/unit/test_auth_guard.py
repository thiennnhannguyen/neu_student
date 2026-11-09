"""Ma trận quyền và danh sách route."""

import pytest
from flask import Blueprint
from sqlalchemy import select

from app import create_app
from app.common.auth_guard import (
    PUBLIC_POLICY,
    can_access_student,
    public_route,
    require_roles,
    resolve_target_student,
)
from app.common.errors import ApiError
from app.extensions import db
from app.models.shared import User

PUBLIC_ENDPOINTS = {
    "health.health",
    "auth.login",
    "auth.me",
    "auth.demo_accounts",
    # Bản build của giao diện, không có dữ liệu (D-115).
    "spa.index",
    "spa.page",
    # Trang xác thực chứng chỉ (CR-04): chỉ trả tên, mô-đun, ngày cấp, hiệu lực.
    "public_certificates.verify_certificate",
}
# gv1 phụ trách SV01 đến SV04, gv2 phụ trách SV05 đến SV07.
OWN_ID = {"sv01": "SV01", "gv1": "user-gv1", "admin": "user-admin", "ht1": "user-ht1"}
ASSIGNED_ID = "SV02"
OUTSIDE_ID = "SV05"
MISSING_ID = "KHONG-CO"


def user_named(username) -> User:
    return db.session.scalar(select(User).where(User.username == username))


MATRIX = [
    # Vai trò, loại id, kết quả: mã sinh viên hoặc mã HTTP.
    ("sv01", "none", "SV01"),
    ("sv01", "own", "SV01"),
    ("sv01", "assigned", 404),
    ("sv01", "outside", 404),
    ("sv01", "missing", 404),
    ("gv1", "none", 422),
    ("gv1", "own", 404),
    ("gv1", "assigned", ASSIGNED_ID),
    ("gv1", "outside", 404),
    ("gv1", "missing", 404),
    ("admin", "none", 422),
    ("admin", "own", 404),
    ("admin", "assigned", ASSIGNED_ID),
    ("admin", "outside", OUTSIDE_ID),
    ("admin", "missing", 404),
    ("ht1", "none", 403),
    ("ht1", "own", 403),
    ("ht1", "assigned", 403),
    ("ht1", "outside", 403),
    ("ht1", "missing", 403),
]


def param_for(username, kind):
    return {
        "none": None,
        "own": OWN_ID[username],
        "assigned": ASSIGNED_ID,
        "outside": OUTSIDE_ID,
        "missing": MISSING_ID,
    }[kind]


@pytest.mark.parametrize(("username", "kind", "expected"), MATRIX)
def test_resolve_target_student_matrix(seeded_app, username, kind, expected):
    user = user_named(username)
    param = param_for(username, kind)

    if isinstance(expected, int):
        with pytest.raises(ApiError) as caught:
            resolve_target_student(user, param)
        assert caught.value.status == expected
    else:
        assert resolve_target_student(user, param).id == expected


def test_matrix_has_every_role_and_kind():
    assert len(MATRIX) == 20
    assert {(u, k) for u, k, _ in MATRIX} == {
        (u, k)
        for u in ("sv01", "gv1", "admin", "ht1")
        for k in ("none", "own", "assigned", "outside", "missing")
    }


def test_empty_student_id_is_treated_as_missing_param(seeded_app):
    assert resolve_target_student(user_named("sv01"), "").id == "SV01"


def test_advisor_without_student_id_names_the_field(seeded_app):
    with pytest.raises(ApiError) as caught:
        resolve_target_student(user_named("gv1"), None)
    assert "student_id" in caught.value.details["fields"]


def test_student_role_without_profile_gets_404(seeded_app):
    user = User(
        id="user-chua-ho-so",
        username="chua-ho-so",
        password_hash="x",
        full_name="Chưa có hồ sơ",
        role_id="role-student",
        is_mock=True,
    )
    db.session.add(user)
    db.session.flush()

    with pytest.raises(ApiError) as caught:
        resolve_target_student(user, None)
    assert caught.value.status == 404


@pytest.mark.parametrize(
    ("username", "student_id", "expected"),
    [
        ("sv01", "SV01", True),
        ("sv01", "SV02", False),
        ("gv1", "SV04", True),
        ("gv1", "SV05", False),
        ("gv2", "SV05", True),
        ("admin", "SV07", True),
        ("admin", MISSING_ID, False),
        ("ht1", "SV01", False),
    ],
)
def test_can_access_student(seeded_app, username, student_id, expected):
    assert can_access_student(user_named(username), student_id) is expected


# --- Danh sách route: giữ vĩnh viễn ---


def route_problems(app):
    """Trả về (route thiếu khai báo, tập route công khai)."""
    missing, public = [], set()
    for rule in app.url_map.iter_rules():
        policy = getattr(app.view_functions[rule.endpoint], "auth_policy", None)
        if policy is None:
            missing.append(rule.endpoint)
        elif policy == PUBLIC_POLICY:
            public.add(rule.endpoint)
    return missing, public


M12_USER_ROUTES = {
    ("GET", "/api/m12/careers"),
    ("GET", "/api/m12/careers/<career_id>"),
    ("GET", "/api/m12/careers/<career_id>/tree"),
    ("GET", "/api/m12/requirements/<requirement_id>"),
    ("GET", "/api/m12/career-goal"),
    ("PUT", "/api/m12/career-goal"),
    ("GET", "/api/m12/career-goal/history"),
    ("GET", "/api/m12/progress/careers/<career_id>"),
    ("GET", "/api/m12/my-careers"),
    ("GET", "/api/m12/related"),
    ("GET", "/api/m12/gallery"),
    ("GET", "/api/m12/careers/slug/<slug>"),
    ("GET", "/api/m12/progress/careers/slug/<slug>"),
    ("GET", "/api/m12/roadmaps/current"),
    ("GET", "/api/m12/roadmaps/<roadmap_id>/versions"),
    ("GET", "/api/m12/roadmaps/<roadmap_id>/proposal"),
}
M12_STUDENT_WRITE_ROUTES = {
    ("PUT", "/api/m12/career-goal"),
    ("POST", "/api/m12/roadmaps/generate"),
    ("PATCH", "/api/m12/roadmaps/<roadmap_id>/items/<item_id>"),
    ("POST", "/api/m12/roadmaps/<roadmap_id>/proposal/accept"),
    ("POST", "/api/m12/roadmaps/<roadmap_id>/proposal/dismiss"),
}
# Giai đoạn 10: mỗi route khai báo đúng vai trò của nó.
READER_NAMES = {"student", "advisor", "admin"}
EVERYONE_NAMES = READER_NAMES | {"support_staff"}
M12_WORK_ROUTES = {
    ("GET", "/api/m12/careers/slug/<slug>/framework"): READER_NAMES,
    ("POST", "/api/m12/modules/<module_id>/attempts"): {"student"},
    ("GET", "/api/m12/modules/<module_id>/review"): {"student"},
    ("GET", "/api/m12/attempts/<attempt_id>"): {"student"},
    ("PUT", "/api/m12/attempts/<attempt_id>/answers/<question_id>"): {"student"},
    ("POST", "/api/m12/attempts/<attempt_id>/submit"): {"student"},
    ("GET", "/api/m12/certificates"): READER_NAMES,
    ("GET", "/api/m12/certificates/<code>"): READER_NAMES,
    ("GET", "/api/m12/evidences"): READER_NAMES,
    ("POST", "/api/m12/evidences"): {"student"},
    ("GET", "/api/m12/evidences/<evidence_id>/attachments/<attachment_id>"): EVERYONE_NAMES,
    ("GET", "/api/m12/evidence-reviews"): {"advisor", "admin"},
    ("GET", "/api/m12/evidence-reviews/<evidence_id>"): {"advisor", "admin"},
    ("POST", "/api/m12/evidence-reviews/<evidence_id>/approve"): {"advisor"},
    ("POST", "/api/m12/evidence-reviews/<evidence_id>/reject"): {"advisor"},
    ("GET", "/api/m12/support-categories"): EVERYONE_NAMES,
    ("GET", "/api/m12/support-requests"): EVERYONE_NAMES,
    ("POST", "/api/m12/support-requests"): {"student"},
    ("GET", "/api/m12/support-requests/<request_id>"): EVERYONE_NAMES,
    ("POST", "/api/m12/support-requests/<request_id>/messages"): EVERYONE_NAMES,
    ("POST", "/api/m12/support-requests/<request_id>/status"): EVERYONE_NAMES,
    ("GET", "/api/m12/support-requests/<request_id>/attachments/<attachment_id>"): EVERYONE_NAMES,
    ("GET", "/api/m12/improvement-plan"): READER_NAMES,
    ("POST", "/api/m12/improvement-plan"): {"student"},
    ("POST", "/api/m12/improvement-plan/<plan_id>/new-risks"): {"student"},
    ("POST", "/api/m12/improvement-plan/<plan_id>/items"): {"student"},
    ("PATCH", "/api/m12/improvement-plan/<plan_id>/items/<item_id>"): {"student"},
    ("DELETE", "/api/m12/improvement-plan/<plan_id>/items/<item_id>"): {"student"},
}
NOTIFICATION_ROUTES = {
    ("GET", "/api/notifications"),
    ("POST", "/api/notifications/<int:notification_id>/read"),
    ("POST", "/api/notifications/read-all"),
}
M12_ADMIN_ROUTES = {
    ("GET", "/api/admin/audit-logs/entities"),
    ("GET", "/api/admin/careers"),
    ("POST", "/api/admin/careers"),
    ("GET", "/api/admin/careers/<career_id>"),
    ("PATCH", "/api/admin/careers/<career_id>"),
    ("DELETE", "/api/admin/careers/<career_id>"),
    ("GET", "/api/admin/careers/<career_id>/versions"),
    ("POST", "/api/admin/careers/<career_id>/versions"),
    ("GET", "/api/admin/skills"),
    ("POST", "/api/admin/skills"),
    ("GET", "/api/admin/skills/<skill_id>"),
    ("PATCH", "/api/admin/skills/<skill_id>"),
    ("DELETE", "/api/admin/skills/<skill_id>"),
    ("GET", "/api/admin/course-skill-mappings"),
    ("POST", "/api/admin/course-skill-mappings"),
    ("GET", "/api/admin/course-skill-mappings/<mapping_id>"),
    ("PATCH", "/api/admin/course-skill-mappings/<mapping_id>"),
    ("DELETE", "/api/admin/course-skill-mappings/<mapping_id>"),
    ("POST", "/api/admin/course-skill-mappings/<mapping_id>/approve"),
    ("GET", "/api/admin/career-versions/<version_id>"),
    ("DELETE", "/api/admin/career-versions/<version_id>"),
    ("POST", "/api/admin/career-versions/<version_id>/publish"),
    ("POST", "/api/admin/career-versions/<version_id>/nodes"),
    ("GET", "/api/admin/career-nodes/<node_id>"),
    ("PATCH", "/api/admin/career-nodes/<node_id>"),
    ("DELETE", "/api/admin/career-nodes/<node_id>"),
    ("POST", "/api/admin/career-nodes/<node_id>/requirements"),
    ("GET", "/api/admin/requirements/<requirement_id>"),
    ("PATCH", "/api/admin/requirements/<requirement_id>"),
    ("DELETE", "/api/admin/requirements/<requirement_id>"),
    ("POST", "/api/admin/requirements/<requirement_id>/approve"),
}


def test_every_route_declares_a_policy_and_public_list_is_exact():
    app = create_app("testing")

    missing, public = route_problems(app)

    assert missing == []
    assert public == PUBLIC_ENDPOINTS


# D-309 (CR-11): API nhận dữ liệu LMS, chỉ quản trị và cố vấn (form LMS Demo).
LMS_ROUTES = {
    ("POST", "/api/lms/sync"),
    ("POST", "/api/lms/preview"),
    ("GET", "/api/lms/form-options"),
    ("GET", "/api/lms/calendar"),
    ("GET", "/api/lms/snapshots/latest"),
}


# D-312: báo cáo tuần. Đang mở, nộp, làm sau: chỉ sinh viên; xem lại: sinh viên, cố vấn, quản trị.
WEEKLY_REPORT_STUDENT_ROUTES = {
    ("GET", "/api/weekly-reports/open"),
    ("POST", "/api/weekly-reports/<course_id>/<int:week_no>/submit"),
    ("POST", "/api/weekly-reports/<course_id>/<int:week_no>/postpone"),
}
WEEKLY_REPORT_READ_ROUTE = ("GET", "/api/weekly-reports")


def test_route_registry_covers_all_expected_api_routes():
    app = create_app("testing")
    rules = {
        (next(iter(rule.methods - {"HEAD", "OPTIONS"})), rule.rule)
        for rule in app.url_map.iter_rules()
    }

    assert rules == {
        ("GET", "/api/public/certificates/<code>"),
        ("GET", "/"),
        ("GET", "/<spa:path>"),
        ("GET", "/api/health"),
        ("POST", "/api/auth/login"),
        ("GET", "/api/auth/demo-accounts"),
        ("POST", "/api/auth/logout"),
        ("GET", "/api/auth/me"),
        ("GET", "/api/students/me"),
        ("PATCH", "/api/students/me/contact"),
        ("GET", "/api/students/<student_id>"),
        ("GET", "/api/admin/audit-logs"),
        ("GET", "/api/admin/students"),
        ("POST", "/api/admin/grade-attempts"),
        ("GET", "/api/advisor/students"),
        ("GET", "/api/m11/semesters"),
        ("GET", "/api/m11/overview"),
        ("GET", "/api/m11/grades"),
        ("GET", "/api/m11/grades/<course_id>/attempts"),
        ("GET", "/api/m11/gpa-trend"),
        ("GET", "/api/m11/credits"),
        ("GET", "/api/m11/curriculum-check"),
        ("GET", "/api/m11/strengths"),
        ("GET", "/api/m11/risks"),
        ("GET", "/api/m11/compare"),
        ("GET", "/api/m11/metrics-glossary"),
        ("GET", "/api/m11/current-courses"),
        ("GET", "/api/m11/courses/<course_id>/prediction"),  # D-314
        *LMS_ROUTES,
        *WEEKLY_REPORT_STUDENT_ROUTES,
        WEEKLY_REPORT_READ_ROUTE,
        *M12_USER_ROUTES,
        *M12_STUDENT_WRITE_ROUTES,
        *M12_WORK_ROUTES,
        *NOTIFICATION_ROUTES,
        *M12_ADMIN_ROUTES,
    }


def test_m11_and_grade_entry_routes_declare_exact_roles():
    """Khai báo đúng ở route, không dựa vào lớp kiểm tra thứ hai trong service."""
    app = create_app("testing")
    readers = {"student", "advisor", "admin"}

    # Khóa gồm cả method: PUT career-goal khác với GET cùng đường dẫn.
    policies = {
        (next(iter(rule.methods - {"HEAD", "OPTIONS"})), rule.rule): set(
            app.view_functions[rule.endpoint].auth_policy
        )
        for rule in app.url_map.iter_rules()
        if rule.rule.startswith(
            ("/api/m11/", "/api/m12/", "/api/admin/", "/api/advisor/", "/api/lms/")
        )
    }

    new_writes = M12_STUDENT_WRITE_ROUTES - M12_USER_ROUTES
    assert len(policies) == (
        14
        + 1
        + 1  # GET /api/m11/current-courses (D-309)
        + 1  # GET /api/m11/courses/<course_id>/prediction (D-314)
        + len(LMS_ROUTES)
        + len(M12_USER_ROUTES)
        + len(new_writes)
        + len(M12_WORK_ROUTES)
        + len(M12_ADMIN_ROUTES)
    )
    for (method, path), roles in policies.items():
        if (method, path) in LMS_ROUTES:
            assert roles == {"admin", "advisor"}, path
        elif (method, path) in M12_WORK_ROUTES:
            assert roles == M12_WORK_ROUTES[(method, path)], path
        elif (method, path) in M12_STUDENT_WRITE_ROUTES:
            assert roles == {"student"}
        elif path.startswith(("/api/m11/", "/api/m12/")):
            assert roles == readers, path
        elif path.startswith("/api/admin/"):
            assert roles == {"admin"}, path
        else:
            assert roles == {"advisor"}, path


def test_registry_catches_route_without_decorator():
    app = create_app("testing")

    @app.get("/api/_quen-khai-bao")
    def forgotten():
        return ""

    assert route_problems(app)[0] == ["forgotten"]


def test_registry_catches_decorator_placed_above_route():
    """Đặt sai thứ tự thì Flask đăng ký hàm chưa được bọc, route không được bảo vệ."""
    app = create_app("testing")
    blueprint = Blueprint("sai_thu_tu", __name__)

    @require_roles("admin")
    @blueprint.get("/api/_sai-thu-tu")
    def wrong_order():
        return ""

    app.register_blueprint(blueprint)

    assert route_problems(app)[0] == ["sai_thu_tu.wrong_order"]


def test_registry_catches_extra_public_route():
    app = create_app("testing")

    @app.get("/api/_cong-khai-them")
    @public_route
    def extra():
        return ""

    assert route_problems(app)[1] == PUBLIC_ENDPOINTS | {"extra"}


@pytest.mark.parametrize("roles", [(), ("giang_vien",), ("admin", "khong-co")])
def test_require_roles_rejects_bad_declaration(roles):
    with pytest.raises(ValueError):
        require_roles(*roles)
