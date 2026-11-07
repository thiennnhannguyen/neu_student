"""Đo p95 của 6 endpoint chính trên CSDL riêng có số sinh viên ×20 (D-277).

Chạy: cd backend && .venv/bin/python -m scripts.perf_p95 [--scale 20]
Không đụng CSDL dev, không đụng fixture. Gọi HTTP thật tới gunicorn 1 worker, tuần tự.
"Lần đầu" là lần gọi đầu của mỗi sinh viên sau khi khởi động lại server, cache còn rỗng.
"Các lần sau" là 2 lần gọi kế tiếp.
"""

import argparse
import http.cookiejar
import json
import math
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
PORT = 8200
BASE = f"http://127.0.0.1:{PORT}"
PASSWORD = "Demo@12345"
TARGET_MS = 300
SEMESTER = "S5"
FETCH = {"X-Requested-With": "fetch", "Content-Type": "application/json"}
# Bảng gắn với sinh viên trong profile demo-k68, cha đứng trước con.
CLONED_TABLES = (
    "advisor_assignments",
    "student_career_goals",
    "skill_evidences",
    "enrollments",
    "grade_attempts",
)


def clone_students(database: Path, scale: int) -> list[str]:
    """Nhân bản mỗi sinh viên mock thành `scale` bản. Trả về mọi tên đăng nhập sinh viên."""
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    students = connection.execute("SELECT * FROM students").fetchall()
    usernames = []
    for student in students:
        user = connection.execute(
            "SELECT * FROM users WHERE id = ?", (student["user_id"],)
        ).fetchone()
        usernames.append(user["username"])
        for copy in range(1, scale):
            suffix = f"-x{copy}"
            _insert(
                connection,
                "users",
                {**dict(user), "id": user["id"] + suffix, "username": user["username"] + suffix},
            )
            _insert(
                connection,
                "students",
                {
                    **dict(student),
                    "id": student["id"] + suffix,
                    "user_id": user["id"] + suffix,
                    "student_code": student["student_code"] + suffix,
                },
            )
            usernames.append(user["username"] + suffix)
            for table in CLONED_TABLES:
                rows = connection.execute(
                    f"SELECT * FROM {table} WHERE student_id = ?",  # noqa: S608
                    (student["id"],),
                ).fetchall()
                for row in rows:
                    values = dict(row)
                    values["id"] = f"{values['id']}{suffix}"
                    values["student_id"] = student["id"] + suffix
                    if "enrollment_id" in values:
                        values["enrollment_id"] = f"{values['enrollment_id']}{suffix}"
                    _insert(connection, table, values)
    connection.commit()
    connection.close()
    return usernames


def _insert(connection: sqlite3.Connection, table: str, values: dict) -> None:
    columns = ", ".join(f'"{name}"' for name in values)
    marks = ", ".join("?" for _ in values)
    connection.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({marks})",  # noqa: S608
        list(values.values()),
    )


def client() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )


def call(opener, path: str, body: dict | None = None, method: str | None = None):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(BASE + path, data=data, headers=FETCH, method=method)
    started = time.perf_counter()
    try:
        with opener.open(request) as response:
            raw, status = response.read(), response.status
    except urllib.error.HTTPError as error:
        raw, status = error.read(), error.code
    elapsed = (time.perf_counter() - started) * 1000
    return status, json.loads(raw or b"{}"), elapsed


def login(username: str):
    opener = client()
    status, _, _ = call(opener, "/api/auth/login", {"username": username, "password": PASSWORD})
    if status != 200:
        raise RuntimeError(f"Không đăng nhập được {username}: {status}")
    return opener


def start_server(env: dict) -> subprocess.Popen:
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "gunicorn",
            "--workers",
            "1",
            "--timeout",
            "120",
            "--bind",
            f"127.0.0.1:{PORT}",
            "app:create_app()",
        ],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        try:
            with urllib.request.urlopen(f"{BASE}/api/health"):
                return server
        except OSError:
            time.sleep(0.2)
    server.kill()
    raise RuntimeError("Server không khởi động được.")


def stop_server(server: subprocess.Popen) -> None:
    server.terminate()
    server.wait(timeout=20)


def p95(samples: list[float]) -> float:
    ordered = sorted(samples)
    return ordered[math.ceil(len(ordered) * 0.95) - 1]


def primary_career(opener) -> str | None:
    _, body, _ = call(opener, "/api/m12/career-goal")
    goal = body.get("goal") or body.get("primary") or {}
    career = goal.get("career") or {}
    return career.get("id") or goal.get("career_id")


def measure(usernames: list[str]) -> tuple[dict, dict, list[str]]:
    cold: dict[str, list[float]] = {}
    warm: dict[str, list[float]] = {}
    errors = []
    for username in usernames:
        opener = login(username)
        career = primary_career(opener) or "career-k68-ai"
        endpoints = {
            "GET /api/m11/overview": "/api/m11/overview",
            "GET /api/m11/grades": "/api/m11/grades",
            "GET /api/m12/progress/careers/{id}": f"/api/m12/progress/careers/{career}",
            "GET /api/m12/gallery": "/api/m12/gallery",
            "GET /api/m12/roadmaps/current": "/api/m12/roadmaps/current",
            "GET /api/notifications": "/api/notifications",
        }
        for name, path in endpoints.items():
            for attempt in range(3):
                status, _, elapsed = call(opener, path)
                if status != 200:
                    errors.append(f"{username} {path}: {status}")
                (cold if attempt == 0 else warm).setdefault(name, []).append(elapsed)
    return cold, warm, errors


def measure_after_new_grade(usernames: list[str]) -> tuple[dict, list[str]]:
    """Trường hợp nặng nhất: điểm mới làm lộ trình lỗi thời, lần đọc đầu phải tính đề xuất."""
    admin = login("admin")
    samples: dict[str, list[float]] = {}
    errors = []
    for username in usernames:
        opener = login(username)
        _, current, _ = call(opener, "/api/m12/roadmaps/current")
        roadmap = current["roadmap"]
        course = next(
            item["course"]["id"]
            for column in roadmap["semesters"]
            for item in column["items"]
            if item["kind"] == "course"
        )
        body = {
            "student_id": current["student_id"],
            "course_id": course,
            "semester_id": SEMESTER,
            "score": "8.0",
        }
        status, _, _ = call(admin, "/api/admin/grade-attempts", body)
        if status != 201:
            errors.append(f"{username} thêm điểm: {status}")
        for path in ("/api/notifications", "/api/m12/roadmaps/current"):
            status, _, elapsed = call(opener, path)
            if status != 200:
                errors.append(f"{username} {path}: {status}")
            samples.setdefault(f"GET {path}", []).append(elapsed)
    return samples, errors


def report(cold: dict, warm: dict, stale: dict, students: int, errors: list[str]) -> str:
    verdict = lambda value: "đạt" if value < TARGET_MS else "không đạt"  # noqa: E731
    lines = [
        f"{students} sinh viên, gunicorn 1 worker, gọi tuần tự, mục tiêu p95 < {TARGET_MS} ms.",
        f"Mỗi endpoint: lần đầu {students} mẫu, các lần sau {students * 2} mẫu. "
        f"Lỗi HTTP: {len(errors)}.",
        "",
        "| Endpoint | Lần đầu p95 (ms) | Đánh giá | Các lần sau p95 (ms) | Đánh giá |",
        "|---|---|---|---|---|",
    ]
    for name in cold:
        first, later = p95(cold[name]), p95(warm[name])
        lines.append(
            f"| `{name}` | {first:.1f} | {verdict(first)} | {later:.1f} | {verdict(later)} |"
        )
    lines += [
        "",
        "Ngay sau khi có điểm mới làm lộ trình lỗi thời (lần đọc đầu):",
        "",
        "| Endpoint | p95 (ms) | Đánh giá |",
        "|---|---|---|",
    ]
    for name, values in stale.items():
        lines.append(f"| `{name}` | {p95(values):.1f} | {verdict(p95(values))} |")
    return "\n".join(lines + errors[:5])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=int, default=20)
    args = parser.parse_args()
    folder = Path(tempfile.mkdtemp(prefix="neu-student-perf-"))
    database = folder / "perf.db"
    env = {
        **os.environ,
        "APP_CONFIG": "local-prod",
        "SESSION_COOKIE_SECURE": "false",
        "SECRET_KEY": "perf-only",
        "DATABASE_URL": f"sqlite:///{database}",
        "UPLOAD_DIR": str(folder / "uploads"),
    }
    flask = [sys.executable, "-m", "flask", "--app", "app"]
    try:
        for command in (["db", "upgrade"], ["seed", "--reset", "--profile", "demo-k68"]):
            subprocess.run(flask + command, cwd=BACKEND, env=env, check=True, capture_output=True)
        usernames = clone_students(database, args.scale)
        server = start_server(env)
        try:
            for username in usernames:
                status, body, _ = call(login(username), "/api/m12/roadmaps/generate", {})
                if status not in (200, 201):
                    raise RuntimeError(f"Không tạo được lộ trình {username}: {status} {body}")
        finally:
            stop_server(server)
        server = start_server(env)
        try:
            cold, warm, errors = measure(usernames)
            stale, stale_errors = measure_after_new_grade(usernames)
        finally:
            stop_server(server)
        print(report(cold, warm, stale, len(usernames), errors + stale_errors))
    finally:
        shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
    main()
