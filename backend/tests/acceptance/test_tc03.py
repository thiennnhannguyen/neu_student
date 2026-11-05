"""TC03: học lại không cộng trùng tín chỉ; GPA đúng với cả best và latest."""

from dataclasses import replace
from decimal import Decimal

import pytest

from app.services.credit_service import credit_summary
from app.services.effective_attempt_service import effective_attempts
from app.services.gpa_service import cumulative_gpa
from app.services.m11_loader import load_student_data


def with_policy(policy):
    data = load_student_data("SV02")
    return replace(data, rule=replace(data.rule, retake_policy=policy))


@pytest.mark.parametrize(
    ("policy", "numerator", "value"),
    [("best", 72, "3.00"), ("latest", 69, "2.88")],
)
def test_cumulative_gpa_for_each_policy(seeded_app, policy, numerator, value):
    result = cumulative_gpa(with_policy(policy), "S4")

    assert (result.numerator, result.denominator) == (Decimal(numerator), 24)
    assert result.value == Decimal(value)


@pytest.mark.parametrize("policy", ["best", "latest"])
def test_retake_does_not_double_count_credits(seeded_app, policy):
    data = with_policy(policy)

    assert credit_summary(data).passed == 25
    assert credit_summary(data).debt == 0
    mau101 = [e for e in effective_attempts(data) if "MAU101" in e.course_ids]
    assert len(mau101) == 1


def test_three_attempts_of_mau101_exist_but_count_once(seeded_app):
    data = load_student_data("SV02")

    assert len([a for a in data.attempts if a.course_id == "MAU101"]) == 3


def test_default_policy_of_k66_is_best(seeded_app):
    assert cumulative_gpa(load_student_data("SV02"), "S4").value == Decimal("3.00")
