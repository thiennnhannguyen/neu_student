"""Kiểm tra vòng: seed không làm mất hay biến dạng dữ liệu."""

import json
from decimal import Decimal

from app.seed.seed import EXPECTED_FILE, FIXTURES_DIR, load_fixture_tables
from tests.helpers import export_tables, same_value
from tests.reference.fixture_reference_calc import reference_all


def test_reference_on_seeded_db_matches_all_expected_results(seeded_app):
    expected = json.loads((FIXTURES_DIR / EXPECTED_FILE).read_text(encoding="utf8"))

    calculated = reference_all(export_tables())

    assert set(calculated) == set(expected)
    assert {k: (expected[k], calculated[k]) for k in expected if expected[k] != calculated[k]} == {}
    assert len(expected) == 235


def test_every_fixture_field_is_stored_unchanged(seeded_app):
    exported = {name: {row["id"]: row for row in rows} for name, rows in export_tables().items()}
    differences = []
    for table, rows in load_fixture_tables().items():
        assert set(exported[table]) == {row["id"] for row in rows}, table
        for row in rows:
            stored = exported[table][row["id"]]
            for key, value in row.items():
                if key == "demo_password":
                    continue
                if not same_value(stored[key], value):
                    differences.append((table, row["id"], key, stored[key], value))
    assert differences == []


def test_scores_read_back_as_exact_decimal(seeded_app):
    rows = {row["id"]: row for row in export_tables()["grade_attempts"]}
    attempt = rows["att-SV01-MAU101-S1"]

    assert attempt["score_10"] == Decimal("8.60")
    assert attempt["grade_4"] == Decimal("4.00")
    assert isinstance(attempt["score_10"], Decimal)


def test_courses_without_code_stay_null_and_separate(seeded_app):
    courses = {row["id"]: row for row in export_tables()["courses"]}

    assert courses["course-cd-a"]["code"] is None
    assert courses["course-cd-b"]["code"] is None
    assert courses["course-cd-a"]["name"] == courses["course-cd-b"]["name"]
