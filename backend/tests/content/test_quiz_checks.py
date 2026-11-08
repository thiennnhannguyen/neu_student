"""Chạy thật câu hỏi có check = "run". Khóa dạng m3q06: mô-đun 3, câu 6 của ngân hàng."""

import base64
import hashlib
import hmac
import json
import logging
import math
import multiprocessing
import os
import random
import secrets
import signal
import socket
import sqlite3
import stat
import subprocess
import sys
import threading
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock

import coverage
import pytest
from flask import Flask, abort, request
from markupsafe import escape
from sqlalchemy import Column, ForeignKey, Integer, create_engine, event, text
from sqlalchemy.orm import Session, declarative_base, relationship, selectinload
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from scripts.backend_modules import MODULES
from scripts.quiz_verification import OUTPUT, render
from tests.helpers import login_as

FRAMEWORK = Path(__file__).resolve().parents[2] / "app/seed/fixtures_demo_k68/framework.json"

CHECKS = {}


def check(key):
    def decorator(function):
        CHECKS[key] = function
        return function

    return decorator


def run_keys():
    return [
        f"m{module['order']}q{number:02d}"
        for module in MODULES
        for number, question in enumerate(module["questions"], start=1)
        if question["check"] == "run"
    ]


def students_db():
    db = sqlite3.connect(":memory:")
    db.executescript(
        """
        CREATE TABLE students (id INT, name TEXT, phone TEXT, deleted_at TEXT);
        INSERT INTO students VALUES (1, 'An', '090', NULL), (2, 'Bình', NULL, NULL),
            (3, 'Chi', '091', NULL);
        CREATE TABLE enrollments (student_id INT, course_id TEXT);
        INSERT INTO enrollments VALUES (1, 'A'), (3, 'A'), (1, 'B');
        """
    )
    return db


def plan(db, sql):
    return " ".join(row[3] for row in db.execute(f"EXPLAIN QUERY PLAN {sql}"))


# --- Mô-đun 1 ---


@check("m1q01")
def _():
    count = 0
    for _i in range(100):
        for _j in range(100):
            count += 1
    assert count == 10_000


@check("m1q02")
def _():
    items = list(range(100_000))
    lookup = set(items)
    probes = [99_999] * 300
    started = time.perf_counter()
    assert all(x in items for x in probes)
    in_list = time.perf_counter() - started
    started = time.perf_counter()
    assert all(x in lookup for x in probes)
    assert in_list > (time.perf_counter() - started) * 10


@check("m1q03")
def _():
    import bisect

    items = [5, 1, 3]
    i = bisect.bisect_left(items, 1)
    assert not (i < len(items) and items[i] == 1)
    ordered = sorted(items)
    assert ordered[bisect.bisect_left(ordered, 1)] == 1


@check("m1q04")
def _():
    stack = []
    for value in (1, 2, 3):
        stack.append(value)
    assert stack.pop() == 3


@check("m1q05")
def _():
    from collections import deque

    graph = {"A": ["B", "C"], "B": ["D"], "C": ["E"], "E": ["D"], "D": []}
    distance = {"A": 0}
    queue = deque(["A"])
    while queue:
        node = queue.popleft()
        for next_node in graph[node]:
            if next_node not in distance:
                distance[next_node] = distance[node] + 1
                queue.append(next_node)
    assert distance["D"] == 2


@check("m1q06")
def _():
    counts = {}
    for x in ["a", "b", "a"]:
        counts[x] = counts.get(x, 0) + 1
    assert counts == {"a": 2, "b": 1}


@check("m1q07")
def _():
    def f(n):
        return n * f(n - 1)

    with pytest.raises(RecursionError):
        f(3)


@check("m1q08")
def _():
    rows = ["a1", "b1", "a2"]
    assert sorted(rows, key=lambda r: r[0]) == ["a1", "a2", "b1"]
    assert rows == ["a1", "b1", "a2"]


@check("m1q10")
def _():
    assert math.comb(5, 2) == 5 * 4 // 2 == 10


@check("m1q11")
def _():
    for a in (True, False):
        for b in (True, False):
            assert (not (a and b)) == ((not a) or (not b))
    assert (not (True and False)) != ((not True) and (not False))


@check("m1q12")
def _():
    assert math.comb(5, 2) == 10


@check("m1q14")
def _():
    graph = {"A": ["B"], "B": ["A"]}

    def dfs(node):
        for next_node in graph[node]:
            dfs(next_node)

    with pytest.raises(RecursionError):
        dfs("A")


@check("m1q15")
def _():
    def has_pair(nums, target):
        seen = set()
        calls = 0
        for x in nums:
            calls += 1
            if target - x in seen:
                return True, calls
            seen.add(x)
        return False, calls

    assert has_pair([1, 2, 3], 5) == (True, 3)
    assert has_pair(list(range(1000)), -1) == (False, 1000)


# --- Mô-đun 2 ---


@check("m2q01")
def _():
    def add(x, items=[]):  # noqa: B006
        items.append(x)
        return items

    a = add(1)
    b = add(2)
    assert a == b == [1, 2]


@check("m2q02")
def _():
    class Animal:
        def name(self):
            return "Animal"

    class Dog(Animal):
        def name(self):
            return "Dog"

    x: Animal = Dog()
    assert x.name() == "Dog"


@check("m2q04")
def _():
    def run():
        try:
            int("x")
        except KeyError:
            return "caught"

    with pytest.raises(ValueError):
        run()


@check("m2q05")
def _():
    code = "import sys\ntry:\n    sys.exit(3)\nexcept:\n    print('nuot')\n"
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert done.returncode == 0
    assert "nuot" in done.stdout


@check("m2q06")
def _():
    class R:
        state = "open"

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.state = "closed"

    with R() as r:
        pass
    assert r.state == "closed"


@check("m2q07")
def _():
    n = 200_000
    tracemalloc.start()
    assert sum(x * x for x in range(n)) == sum([x * x for x in range(1)]) + sum(
        x * x for x in range(n)
    )
    tracemalloc.reset_peak()
    sum(x * x for x in range(n))
    generator_peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.reset_peak()
    sum([x * x for x in range(n)])  # noqa: C419
    list_peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert list_peak > generator_peak * 10


@check("m2q08")
def _():
    @dataclass
    class P:
        x: int

    assert P(1) == P(1)


@check("m2q12")
def _():
    class Service:
        def __init__(self, repo):
            self.repo = repo

        def add(self, x):
            self.repo.save(x)

    repo = Mock()
    Service(repo).add(1)
    repo.save.assert_called_once_with(1)


@check("m2q13")
def _():
    a = [1, 2, 3]
    b = a
    b.append(4)
    assert a == [1, 2, 3, 4]


@check("m2q15")
def _():
    class AlreadyDropped(Exception):
        pass

    with pytest.raises(AlreadyDropped):
        raise AlreadyDropped()


# --- Mô-đun 3 ---


@check("m3q01")
def _():
    rows = students_db().execute(
        "SELECT s.name, e.course_id FROM students s "
        "LEFT JOIN enrollments e ON e.student_id = s.id WHERE s.name = 'Bình'"
    )
    assert rows.fetchall() == [("Bình", None)]


@check("m3q02")
def _():
    assert students_db().execute("SELECT COUNT(*), COUNT(phone) FROM students").fetchone() == (3, 2)


@check("m3q03")
def _():
    db = students_db()
    assert db.execute("SELECT COUNT(*) FROM students WHERE deleted_at = NULL").fetchone() == (0,)
    assert db.execute("SELECT COUNT(*) FROM students WHERE deleted_at IS NULL").fetchone() == (3,)


@check("m3q04")
def _():
    db = students_db()
    good = "SELECT course_id FROM enrollments GROUP BY course_id HAVING COUNT(*) > 1"
    assert db.execute(good).fetchall() == [("A",)]
    with pytest.raises(sqlite3.OperationalError):
        db.execute("SELECT course_id FROM enrollments WHERE COUNT(*) > 1 GROUP BY course_id")


@check("m3q06")
def _():
    """Theo yêu cầu: ADD COLUMN NOT NULL không DEFAULT trên bảng có dữ liệu bị từ chối."""
    db = students_db()
    with pytest.raises(sqlite3.OperationalError, match="NOT NULL"):
        db.execute("ALTER TABLE students ADD COLUMN email TEXT NOT NULL")
    db.execute("ALTER TABLE students ADD COLUMN email TEXT")
    db.execute("UPDATE students SET email = name || '@x.vn'")
    assert db.execute("SELECT COUNT(*) FROM students WHERE email IS NULL").fetchone() == (0,)


@check("m3q07")
def _():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE grades (student_id INT, semester_id INT, score INT)")
    db.execute("CREATE INDEX i ON grades (student_id, semester_id)")
    assert "USING INDEX i" in plan(db, "SELECT score FROM grades WHERE student_id = 1")
    assert "USING INDEX i" in plan(
        db, "SELECT score FROM grades WHERE student_id = 1 AND semester_id = 2"
    )
    assert "SCAN" in plan(db, "SELECT score FROM grades WHERE semester_id = 2")
    ordered = plan(db, "SELECT score FROM grades WHERE student_id = 1 ORDER BY semester_id")
    assert "USING INDEX i" in ordered
    assert "TEMP B-TREE" not in ordered


@check("m3q08")
def _():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE users (id INT, email TEXT, name TEXT)")
    db.execute("CREATE INDEX i_email ON users (email)")
    query = "SELECT * FROM users WHERE lower(email) = 'a@neu.vn'"
    assert "SCAN" in plan(db, query)
    db.execute("CREATE INDEX i_lower ON users (lower(email))")
    assert "USING INDEX i_lower" in plan(db, query)


@check("m3q10")
def _(tmp_path):
    """Tiến trình thật chết giữa transaction, đọc lại từ tiến trình này."""
    path = tmp_path / "bank.db"
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE accounts (id TEXT, balance INT)")
    db.execute("INSERT INTO accounts VALUES ('A', 500), ('B', 0)")
    db.commit()
    db.close()
    code = (
        "import os, sqlite3, sys\n"
        "db = sqlite3.connect(sys.argv[1])\n"
        "db.execute(\"UPDATE accounts SET balance = balance - 100 WHERE id = 'A'\")\n"
        "os._exit(9)\n"
    )
    done = subprocess.run([sys.executable, "-c", code, str(path)])
    assert done.returncode == 9
    rows = dict(sqlite3.connect(path).execute("SELECT id, balance FROM accounts"))
    assert rows == {"A": 500, "B": 0}


@check("m3q11")
def _(tmp_path):
    """2 kết nối riêng cùng UPDATE có điều kiện: đúng 1 kết nối thành công."""
    path = tmp_path / "slots.db"
    first = sqlite3.connect(path, timeout=5)
    first.execute("CREATE TABLE courses (id TEXT, slots INT)")
    first.execute("INSERT INTO courses VALUES ('C', 1)")
    first.commit()
    second = sqlite3.connect(path, timeout=5)
    sql = "UPDATE courses SET slots = slots - 1 WHERE id = ? AND slots > 0"
    counts = []
    for connection in (first, second):
        counts.append(connection.execute(sql, ("C",)).rowcount)
        connection.commit()
    assert counts == [1, 0]
    assert first.execute("SELECT slots FROM courses").fetchone() == (0,)


@check("m3q12")
def _():
    base = declarative_base()

    class Student(base):
        __tablename__ = "students"
        id = Column(Integer, primary_key=True)
        enrollments = relationship("Enrollment")

    class Enrollment(base):
        __tablename__ = "enrollments"
        id = Column(Integer, primary_key=True)
        student_id = Column(ForeignKey("students.id"))

    engine = create_engine("sqlite://")
    base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([Student(id=i) for i in range(1, 51)])
        session.commit()
    count = [0]

    def counter(_connection, _cursor, statement, *_args):
        count[0] += statement.startswith("SELECT")

    event.listen(engine, "before_cursor_execute", counter)
    with Session(engine) as session:
        for student in session.query(Student).limit(50).all():
            len(student.enrollments)
    assert count[0] == 51
    count[0] = 0
    with Session(engine) as session:
        query = session.query(Student).options(selectinload(Student.enrollments)).limit(50)
        for student in query.all():
            len(student.enrollments)
    assert count[0] == 2


@check("m3q15")
def _():
    """Chuỗi tấn công lấy được mọi dòng khi nối chuỗi, không lấy được dòng nào khi có tham số."""
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE users (username TEXT)")
    db.execute("INSERT INTO users VALUES ('a'), ('b')")
    attack = "' OR '1'='1"
    concatenated = f"SELECT * FROM users WHERE username = '{attack}'"  # noqa: S608
    assert len(db.execute(concatenated).fetchall()) == 2
    assert db.execute("SELECT * FROM users WHERE username = ?", (attack,)).fetchall() == []
    engine = create_engine("sqlite://")
    with engine.connect() as connection:
        connection.execute(text("CREATE TABLE users (username TEXT)"))
        connection.execute(text("INSERT INTO users VALUES ('a')"))
        sql = text("SELECT * FROM users WHERE username = :u")
        assert connection.execute(sql, {"u": attack}).fetchall() == []


# --- Mô-đun 4 ---


def _increase(_value):
    global SHARED
    SHARED = 1
    return SHARED


SHARED = 0


@check("m4q01")
def _():
    context = multiprocessing.get_context("spawn")
    with context.Pool(1) as pool:
        assert pool.apply(_increase, (0,)) == 1
    assert SHARED == 0


@check("m4q03")
def _():
    """Cùng thứ tự khóa thì 2 luồng lặp nhiều lần vẫn kết thúc, không kẹt."""
    a, b = threading.Lock(), threading.Lock()

    def work():
        for _i in range(2000):
            with a, b:
                pass

    threads = [threading.Thread(target=work, daemon=True) for _i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    assert not any(thread.is_alive() for thread in threads)


@check("m4q04")
def _():
    started = time.perf_counter()
    with ThreadPoolExecutor(10) as pool:
        list(pool.map(lambda _x: time.sleep(0.05), range(10)))
    assert time.perf_counter() - started < 0.5 * 0.6


@check("m4q05")
def _():
    code = (
        "import signal, sys, time\n"
        "signal.signal(signal.SIGTERM, lambda *a: (print('don dep', flush=True), sys.exit(0)))\n"
        "print('san sang', flush=True)\n"
        "time.sleep(30)\n"
    )
    for sent, cleaned in ((signal.SIGTERM, True), (signal.SIGKILL, False)):
        process = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        assert process.stdout.readline().strip() == "san sang"
        process.send_signal(sent)
        output = process.communicate(timeout=10)[0]
        assert ("don dep" in output) is cleaned


@check("m4q06")
def _(tmp_path):
    path = tmp_path / "secret.env"
    path.write_text("x")
    os.chmod(path, 0o640)
    mode = stat.S_IMODE(path.stat().st_mode)
    assert mode & stat.S_IRUSR and mode & stat.S_IWUSR
    assert mode & stat.S_IRGRP and not mode & stat.S_IWGRP
    assert not mode & stat.S_IRWXO


@check("m4q10")
def _():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    with pytest.raises(ConnectionRefusedError):
        socket.create_connection(("127.0.0.1", port), timeout=2)


@check("m4q14")
def _():
    context = multiprocessing.get_context("spawn")
    with context.Pool(1) as other:
        assert other.apply(_increase, (0,)) == 1
        assert SHARED == 0


@check("m4q15")
def _():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]
        done = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)
    assert str(os.getpid()) in done.stdout


# --- Mô-đun 5 ---


def toy_app():
    app = Flask(__name__)
    books = {1: {"title": "A"}}

    @app.delete("/books/<int:book_id>")
    def delete(book_id):
        books.pop(book_id)
        return "", 204

    @app.get("/books/<int:book_id>")
    def get(book_id):
        book = books.get(book_id)
        if book is None:
            abort(404)
        return book

    @app.post("/books")
    def create():
        return request.get_json(), 201

    @app.post("/upload")
    def upload():
        return str(len(request.get_data()))

    return app


@check("m5q01")
def _():
    client = toy_app().test_client()
    assert client.post("/books", json={"title": "B"}).status_code == 201


@check("m5q02")
def _():
    response = toy_app().test_client().delete("/books/1")
    assert response.status_code == 204
    assert response.data == b""


@check("m5q03")
def _(demo_app):
    assert demo_app.test_client().get("/api/m11/overview").status_code == 401


@check("m5q04")
def _(demo_app):
    client = login_as(demo_app, "demo05")
    assert client.get("/api/admin/audit-logs").status_code == 403


@check("m5q05")
def _():
    client = toy_app().test_client()
    response = client.post("/books", data='{"title":', content_type="application/json")
    assert response.status_code == 400


@check("m5q10")
def _():
    from app.config import ProductionConfig

    assert ProductionConfig.SESSION_COOKIE_HTTPONLY is True
    assert ProductionConfig.SESSION_COOKIE_SECURE is True
    assert ProductionConfig.SESSION_COOKIE_SAMESITE == "Lax"


@check("m5q13")
def _():
    assert toy_app().test_client().get("/books/99").status_code == 404


@check("m5q14")
def _():
    app = toy_app()
    app.config["MAX_CONTENT_LENGTH"] = 10
    assert app.test_client().post("/upload", data=b"x" * 100).status_code == 413


# --- Mô-đun 6 ---


@check("m6q05")
def _():
    assert [2**attempt for attempt in range(3)] == [1, 2, 4]


@check("m6q07")
def _(demo_app):
    """Chính cơ chế của dự án: thêm minh chứng làm data_version đổi, khóa cache đổi theo."""
    from app.common.data_version import bump_data_version
    from app.extensions import db
    from app.models.shared import Student

    with demo_app.app_context():
        student = db.session.get(Student, "DEMO05")
        before = f"gpa:{student.id}:{student.data_version}"
        bump_data_version(student)
        db.session.commit()
        db.session.refresh(student)
        assert f"gpa:{student.id}:{student.data_version}" != before


@check("m6q12")
def _():
    secret, body = b"k", b"{}"
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    assert hmac.compare_digest(expected, hmac.new(secret, body, hashlib.sha256).hexdigest())
    assert not hmac.compare_digest(expected, hmac.new(b"x", body, hashlib.sha256).hexdigest())


@check("m6q15")
def _(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    assert os.environ.get("SECRET_KEY", "dev") == "dev"


# --- Mô-đun 7 ---


@check("m7q05")
def _():
    db = sqlite3.connect(":memory:")
    db.executescript(
        """
        CREATE TABLE students (id INT PRIMARY KEY);
        CREATE TABLE courses (id INT PRIMARY KEY);
        CREATE TABLE enrollments (student_id INT REFERENCES students, course_id INT
            REFERENCES courses, score INT, UNIQUE (student_id, course_id));
        INSERT INTO students VALUES (1), (2);
        INSERT INTO courses VALUES (10), (20);
        INSERT INTO enrollments VALUES (1, 10, 8), (1, 20, 7), (2, 10, 6);
        """
    )
    per_student = "SELECT COUNT(*) FROM enrollments WHERE student_id = 1"
    per_course = "SELECT COUNT(*) FROM enrollments WHERE course_id = 10"
    assert db.execute(per_student).fetchone() == (2,)
    assert db.execute(per_course).fetchone() == (2,)


@check("m7q06")
def _():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE students (id INT PRIMARY KEY)")
    db.execute("INSERT INTO students VALUES (1)")
    db.execute("CREATE TABLE plain (student_id INT REFERENCES students)")
    db.executemany("INSERT INTO plain VALUES (?)", [(1,), (1,)])
    db.execute("CREATE TABLE cards (student_id INT UNIQUE REFERENCES students)")
    db.execute("INSERT INTO cards VALUES (1)")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO cards VALUES (1)")


@check("m7q11")
def _():
    assert 200 * 100 // 1000 == 20


# --- Mô-đun 8 ---


@check("m8q01")
def _():
    def right(score):
        return score >= 4

    def wrong(score):
        return score > 4

    assert right(4.0) != wrong(4.0)
    assert right(3.9) == wrong(3.9) is False
    assert right(5.5) == wrong(5.5) is True


@check("m8q02")
def _():
    def calculate_gpa(_scores):
        return -100

    def test_gpa():
        calculate_gpa([8, 9])

    assert test_gpa() is None


@check("m8q03")
def _(tmp_path):
    source = tmp_path / "branchy.py"
    source.write_text("def f(x):\n    y = 0\n    if x > 0:\n        y = x\n    return y\n\nf(5)\n")
    measure = coverage.Coverage(branch=True, data_file=None, include=[str(source)])
    measure.start()
    exec(compile(source.read_text(), str(source), "exec"), {})  # noqa: S102
    measure.stop()
    analysis = measure._analyze(str(source))  # noqa: SLF001
    assert analysis.missing == set()
    assert analysis.missing_branch_arcs() == {3: [5]}


@check("m8q05")
def _():
    shared = []

    def first():
        shared.append(1)
        assert len(shared) == 1

    def second():
        shared.append(2)
        assert len(shared) == 1

    second()
    shared.clear()
    first()
    with pytest.raises(AssertionError):
        second()


@check("m8q06")
def _():
    assert 0.1 + 0.2 != 0.3
    assert 0.1 + 0.2 == pytest.approx(0.3)


@check("m8q07")
def _(tmp_path):
    test_file = tmp_path / "test_param.py"
    test_file.write_text(
        "import pytest\n"
        "def to_letter(s):\n    return {9: 'A', 7: 'B', 5: 'C'}[s]\n"
        "@pytest.mark.parametrize('score,letter', [(9, 'A'), (7, 'B'), (5, 'C')])\n"
        "def test_letter(score, letter):\n    assert to_letter(score) == letter\n"
    )
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--no-cov",
            "-p",
            "no:cacheprovider",
            test_file.name,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert "3 passed" in done.stdout


@check("m8q14")
def _():
    from datetime import datetime

    def is_late(deadline, now):
        return now > deadline

    deadline = datetime(2026, 1, 1)
    assert is_late(deadline, datetime(2026, 1, 2))
    assert not is_late(deadline, datetime(2025, 12, 31))


# --- Mô-đun 9 ---


@check("m9q01")
def _():
    hashed = generate_password_hash("abc")
    assert check_password_hash(hashed, "abc")
    assert not check_password_hash(hashed, "abd")
    assert hashlib.sha256(b"abc").hexdigest() == hashlib.sha256(b"abc").hexdigest()
    assert base64.b64decode(base64.b64encode(b"abc")) == b"abc"


@check("m9q02")
def _():
    assert generate_password_hash("abc") != generate_password_hash("abc")


@check("m9q04")
def _():
    app = Flask(__name__)

    @app.get("/")
    def page():
        return "<p>" + request.args["name"] + "</p>"

    body = app.test_client().get("/?name=<script>alert(1)</script>").get_data(as_text=True)
    assert "<script>alert(1)</script>" in body


@check("m9q05")
def _():
    assert str(escape("<b>")) == "&lt;b&gt;"


@check("m9q06")
def _(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    (tmp_path / "secret").write_text("x")
    joined = os.path.join(uploads, "../secret")
    assert os.path.exists(joined)
    assert not os.path.commonpath([os.path.realpath(joined), uploads]) == str(uploads)
    assert "/" not in secure_filename("../../etc/passwd")
    assert ".." not in secure_filename("../../etc/passwd")


@check("m9q09")
def _():
    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    secret = b"k"
    head, body = part({"alg": "HS256"}), part({"sub": "7"})
    signature = hmac.new(secret, f"{head}.{body}".encode(), hashlib.sha256).hexdigest()
    payload = body + "=" * (-len(body) % 4)
    assert json.loads(base64.urlsafe_b64decode(payload)) == {"sub": "7"}
    tampered = part({"sub": "8"})
    forged = hmac.new(secret, f"{head}.{tampered}".encode(), hashlib.sha256).hexdigest()
    assert signature != forged


@check("m9q13")
def _():
    app = Flask(__name__)
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/")
    def page():
        raise ValueError("SELECT mat_khau FROM users")

    response = app.test_client().get("/")
    assert response.status_code == 500
    assert "SELECT" not in response.get_data(as_text=True)


@check("m9q14")
def _():
    random.seed(1)
    first = random.random()
    random.seed(1)
    assert random.random() == first
    assert secrets.token_urlsafe(16) != secrets.token_urlsafe(16)


# --- Mô-đun 10 ---


def git(cwd, *args):
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "a",
        "GIT_AUTHOR_EMAIL": "a@a",
        "GIT_COMMITTER_NAME": "a",
        "GIT_COMMITTER_EMAIL": "a@a",
    }
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, env=env
    ).stdout


def repo_with_commit(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("1")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "one")
    (tmp_path / "a.txt").write_text("2")
    git(tmp_path, "commit", "-qam", "two")
    return tmp_path


@check("m10q05")
def _(tmp_path):
    repo = repo_with_commit(tmp_path)
    head = git(repo, "rev-parse", "HEAD")
    git(repo, "revert", "--no-edit", "HEAD")
    assert git(repo, "rev-parse", "HEAD~1") == head
    # fetch không có remote: không đổi nhánh hiện tại.
    git(repo, "fetch", "--all", "-q")
    assert git(repo, "rev-parse", "HEAD~1") == head


@check("m10q06")
def _(tmp_path):
    repo = repo_with_commit(tmp_path)
    git(repo, "revert", "--no-edit", "HEAD")
    assert len(git(repo, "log", "--oneline").splitlines()) == 3
    assert (repo / "a.txt").read_text() == "1"


@check("m10q09")
def _(caplog):
    logger = logging.getLogger("m10q09")
    logger.setLevel(logging.WARNING)
    with caplog.at_level(logging.WARNING, logger="m10q09"):
        logger.info("a")
        logger.warning("b")
    assert [record.getMessage() for record in caplog.records] == ["b"]


@check("m10q12")
def _(demo_app):
    response = demo_app.test_client().get("/api/health")
    assert response.status_code == 200
    assert set(response.get_json()) == {"is_mock", "status"}


@check("m10q13")
def _():
    samples = [50] * 98 + [2500, 2500]
    ordered = sorted(samples)
    assert sum(samples) // len(samples) == 99
    assert ordered[math.ceil(len(ordered) * 0.99) - 1] == 2500


# --- Khớp với ngân hàng câu hỏi ---


def test_every_run_question_has_a_real_check_and_theory_has_none():
    assert set(CHECKS) == set(run_keys())


@pytest.mark.parametrize("key", sorted(CHECKS))
def test_question(key, request):
    function = CHECKS[key]
    names = function.__code__.co_varnames[: function.__code__.co_argcount]
    function(**{name: request.getfixturevalue(name) for name in names})


def test_verification_document_is_up_to_date():
    assert OUTPUT.read_text(encoding="utf8") == render()


def test_theory_questions_are_marked_reviewed_by_the_project_manager():
    framework = json.loads(FRAMEWORK.read_text(encoding="utf8"))
    rows = framework["quiz_questions"]
    reviewed = [row for row in rows if row["verification"] == "review"]
    assert len(reviewed) == 73
    assert len([row for row in rows if row["verification"] == "run"]) == 77
    assert {(row["reviewed_by"], row["reviewed_on"]) for row in reviewed} == {
        ("quản lý dự án", "2026-11-08")
    }
    assert all(row["reviewed_by"] is None for row in rows if row["verification"] == "run")


def test_reviewed_wording_of_module_7():
    framework = json.loads(FRAMEWORK.read_text(encoding="utf8"))
    questions = {row["id"]: row for row in framework["quiz_questions"]}
    options = {row["id"]: row for row in framework["quiz_options"]}
    assert options["q-m7-01-c"]["text"] == "Luồng ngoại lệ (luồng thay thế)"
    assert options["q-m7-01-c"]["is_correct"]
    assert questions["q-m7-01"]["explanation"].endswith(
        "Mỗi luồng ngoại lệ thường ứng với một mã lỗi của API."
    )
    assert options["q-m7-09-b"]["is_correct"]
    assert questions["q-m7-09"]["explanation"].endswith(
        "Trong UML, sự kiện theo thời gian được mô hình hóa bằng tác nhân Thời gian/Bộ định thời "
        "vì nó khởi phát use case từ bên ngoài hệ thống."
    )
