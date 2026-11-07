"""Sinh docs/ROUTES.md từ app.url_map: mọi route kèm chính sách quyền.

Chạy: cd backend && .venv/bin/python -m scripts.list_routes
Test test_routes_doc báo lỗi nếu file lệch với route thật.
"""

from pathlib import Path

from flask import Flask

from app import create_app
from app.common.auth_guard import PUBLIC_POLICY

OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "ROUTES.md"
HEADER = """# Danh sách route

Sinh tự động từ `app.url_map` bằng `python -m scripts.list_routes`, không sửa tay.
Chính sách `public` là không cần đăng nhập. Còn lại là các vai trò được gọi; ngoài phạm vi dữ liệu
thì service trả 404. Route ghi (POST, PUT, PATCH, DELETE) còn cần header `X-Requested-With: fetch`.
"""


def route_rows(app: Flask) -> list[tuple[str, str, str]]:
    rows = []
    for rule in app.url_map.iter_rules():
        policy = app.view_functions[rule.endpoint].auth_policy
        allowed = "public" if policy == PUBLIC_POLICY else ", ".join(sorted(policy))
        for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            rows.append((rule.rule, method, allowed))
    return sorted(rows)


def render(app: Flask) -> str:
    rows = route_rows(app)
    public = [row for row in rows if row[2] == "public"]
    lines = [HEADER, f"Tổng {len(rows)} route, {len(public)} route công khai.", ""]
    lines += ["## Route công khai", "", "| Đường dẫn | Phương thức |", "|---|---|"]
    lines += [f"| `{path}` | {method} |" for path, method, _ in public]
    lines += ["", "## Mọi route", "", "| Đường dẫn | Phương thức | Chính sách |", "|---|---|---|"]
    lines += [f"| `{path}` | {method} | {allowed} |" for path, method, allowed in rows]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT.write_text(render(create_app("testing")), encoding="utf8")


if __name__ == "__main__":
    main()
