"""TC05: cùng số liệu, quy chế khác khóa thì mức cảnh báo khác nhau."""

from decimal import Decimal

from app.services.credit_service import credit_summary
from app.services.gpa_service import cumulative_gpa
from app.services.m11_loader import load_student_data
from app.services.risk_service import assess_risk


def test_sv04_and_sv06_have_same_numbers(seeded_app):
    sv04, sv06 = load_student_data("SV04"), load_student_data("SV06")

    assert cumulative_gpa(sv04).value == cumulative_gpa(sv06).value == Decimal("1.81")
    assert credit_summary(sv04).passed == credit_summary(sv06).passed == 19
    assert credit_summary(sv04).debt == credit_summary(sv06).debt == 6


def test_sv04_is_warning_under_k66(seeded_app):
    risk = assess_risk(load_student_data("SV04"))

    assert risk.overall == "warning"
    assert risk.meta.rule_version == "K66-mau-v1"
    levels = {o.rule_code: o.level for o in risk.outcomes}
    assert levels == {"gpa": "warning", "debt": "warning", "registration": "normal"}


def test_sv06_is_normal_under_k67(seeded_app):
    risk = assess_risk(load_student_data("SV06"))

    assert risk.overall == "normal"
    assert risk.meta.rule_version == "K67-mau-v1"
    assert {o.level for o in risk.outcomes} == {"normal"}


def test_evidence_shows_thresholds_of_own_cohort(seeded_app):
    sv04 = assess_risk(load_student_data("SV04"))
    sv06 = assess_risk(load_student_data("SV06"))

    gpa04 = next(o for o in sv04.outcomes if o.rule_code == "gpa")
    gpa06 = next(o for o in sv06.outcomes if o.rule_code == "gpa")
    assert gpa04.evidence["warning_below"] == Decimal("2.00")
    assert gpa06.evidence["warning_below"] == Decimal("1.20")
    assert "tham khảo" in sv04.disclaimer
