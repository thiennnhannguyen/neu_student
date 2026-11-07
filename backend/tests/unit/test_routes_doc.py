"""docs/ROUTES.md phải khớp route thật; danh sách công khai đúng như đã duyệt."""

from app import create_app
from scripts.list_routes import OUTPUT, render, route_rows

APPROVED_PUBLIC = {
    ("/", "GET"),
    ("/<spa:path>", "GET"),
    ("/api/auth/demo-accounts", "GET"),
    ("/api/auth/login", "POST"),
    ("/api/auth/me", "GET"),
    ("/api/health", "GET"),
}


def test_routes_doc_is_up_to_date():
    assert OUTPUT.read_text(encoding="utf8") == render(create_app("testing"))


def test_public_routes_are_exactly_the_approved_list():
    rows = route_rows(create_app("testing"))

    assert {(path, method) for path, method, allowed in rows if allowed == "public"} == (
        APPROVED_PUBLIC
    )


def test_every_row_has_a_policy():
    assert all(allowed for _, _, allowed in route_rows(create_app("testing")))
