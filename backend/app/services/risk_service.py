"""Cảnh báo học vụ (M11-09). Thêm quy tắc: thêm dữ liệu và một hàm có @register_rule."""

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from app.services.credit_service import credit_summary
from app.services.data_quality_service import build_meta
from app.services.effective_attempt_service import effective_attempts
from app.services.gpa_service import cumulative_gpa
from app.services.m11_types import (
    CreditSummary,
    GpaResult,
    RiskAssessment,
    RuleOutcome,
    RuleRef,
    StudentData,
)

LEVEL_NORMAL = "normal"
LEVEL_WATCH = "watch"
LEVEL_WARNING = "warning"
LEVEL_INSUFFICIENT = "insufficient_data"
SEVERITY = {LEVEL_NORMAL: 0, LEVEL_WATCH: 1, LEVEL_WARNING: 2}
DISCLAIMER = "Cảnh báo tham khảo, không phải quyết định học vụ chính thức"


@dataclass(frozen=True)
class RiskFacts:
    rule: RuleRef
    gpa: GpaResult
    credits: CreditSummary
    has_results: bool


@dataclass(frozen=True)
class RuleCheck:
    level: str
    reason: str
    evidence: dict


RULE_REGISTRY: dict[str, Callable[[RiskFacts], RuleCheck]] = {}


def register_rule(code: str):
    def decorator(check):
        RULE_REGISTRY[code] = check
        return check

    return decorator


def _is_below(numerator: Decimal, denominator: int, threshold: Decimal) -> bool:
    """So bằng nhân chéo trên giá trị chưa làm tròn (Q69)."""
    return numerator < threshold * denominator


@register_rule("gpa")
def _gpa_rule(facts: RiskFacts) -> RuleCheck:
    gpa, rule = facts.gpa, facts.rule
    evidence = {
        "numerator": gpa.numerator,
        "denominator": gpa.denominator,
        "value": gpa.value,
        "watch_below": rule.gpa_watch_below,
        "warning_below": rule.gpa_warning_below,
    }
    if gpa.denominator == 0:
        return RuleCheck(LEVEL_INSUFFICIENT, "Chưa có kết quả tính GPA.", evidence)
    if _is_below(gpa.numerator, gpa.denominator, rule.gpa_warning_below):
        return RuleCheck(
            LEVEL_WARNING,
            f"GPA tích lũy {gpa.value} dưới ngưỡng cảnh báo {rule.gpa_warning_below}.",
            evidence,
        )
    if _is_below(gpa.numerator, gpa.denominator, rule.gpa_watch_below):
        return RuleCheck(
            LEVEL_WATCH,
            f"GPA tích lũy {gpa.value} dưới ngưỡng chú ý {rule.gpa_watch_below}.",
            evidence,
        )
    return RuleCheck(
        LEVEL_NORMAL,
        f"GPA tích lũy {gpa.value} không dưới ngưỡng chú ý {rule.gpa_watch_below}.",
        evidence,
    )


@register_rule("debt")
def _debt_rule(facts: RiskFacts) -> RuleCheck:
    debt, rule = facts.credits.debt, facts.rule
    evidence = {
        "debt_credits": debt,
        "watch_from": rule.debt_watch_from,
        "warning_from": rule.debt_warning_from,
    }
    if not facts.has_results:
        return RuleCheck(LEVEL_INSUFFICIENT, "Chưa có kết quả học tập.", evidence)
    if debt >= rule.debt_warning_from:
        return RuleCheck(
            LEVEL_WARNING,
            f"Đang nợ {debt} tín chỉ, từ ngưỡng cảnh báo {rule.debt_warning_from}.",
            evidence,
        )
    if debt >= rule.debt_watch_from:
        return RuleCheck(
            LEVEL_WATCH,
            f"Đang nợ {debt} tín chỉ, từ ngưỡng chú ý {rule.debt_watch_from}.",
            evidence,
        )
    return RuleCheck(
        LEVEL_NORMAL, f"Đang nợ {debt} tín chỉ, dưới ngưỡng chú ý {rule.debt_watch_from}.", evidence
    )


@register_rule("registration")
def _registration_rule(facts: RiskFacts) -> RuleCheck:
    registered, rule = facts.credits.registered, facts.rule
    evidence = {
        "registered_credits": registered,
        "min_credits": rule.registration_min_credits,
        "max_credits": rule.registration_max_credits,
    }
    allowed = f"{rule.registration_min_credits}–{rule.registration_max_credits}"
    if registered == 0:
        return RuleCheck(LEVEL_INSUFFICIENT, "Không có đăng ký ở kỳ đang xem.", evidence)
    if rule.registration_min_credits <= registered <= rule.registration_max_credits:
        return RuleCheck(
            LEVEL_NORMAL, f"Đăng ký {registered} tín chỉ, trong khoảng {allowed}.", evidence
        )
    return RuleCheck(
        LEVEL_WATCH, f"Đăng ký {registered} tín chỉ, ngoài khoảng {allowed}.", evidence
    )


def _overall_level(outcomes: tuple[RuleOutcome, ...]) -> str:
    """Mức cao nhất, bỏ qua insufficient_data. Không có quy tắc nào đủ dữ liệu thì là normal."""
    levels = [o.level for o in outcomes if o.level != LEVEL_INSUFFICIENT]
    return max(levels, key=SEVERITY.__getitem__, default=LEVEL_NORMAL)


def _unknown_rule_outcomes() -> tuple[RuleOutcome, ...]:
    return tuple(
        RuleOutcome(code, LEVEL_INSUFFICIENT, "Không tìm thấy quy chế của khóa.", {}, None)
        for code in RULE_REGISTRY
    )


def assess_risk(data: StudentData) -> RiskAssessment:
    if data.rule is None:
        outcomes = _unknown_rule_outcomes()
    else:
        facts = RiskFacts(
            rule=data.rule,
            gpa=cumulative_gpa(data),
            credits=credit_summary(data),
            has_results=bool(effective_attempts(data)),
        )
        checks = {code: check(facts) for code, check in RULE_REGISTRY.items()}
        outcomes = tuple(
            RuleOutcome(code, result.level, result.reason, result.evidence, data.rule.rule_version)
            for code, result in checks.items()
        )
    return RiskAssessment(
        overall=_overall_level(outcomes),
        outcomes=outcomes,
        disclaimer=DISCLAIMER,
        meta=build_meta(data),
    )
