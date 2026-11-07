"""Kế hoạch cải thiện (M12-10). Mẫu hành động lấy từ dữ liệu theo mã quy tắc của M11."""

from sqlalchemy import func, select

from app.common import clock
from app.common.errors import ApiError
from app.extensions import db
from app.models.m12 import ImprovementPlan, ImprovementPlanItem, RiskActionTemplate
from app.models.shared import Student
from app.services import m11_public
from app.services.career_api_service import iso_time

ACTIVE = "active"
ACTIVE_LEVELS = ("watch", "warning")
TITLE = "Kế hoạch cải thiện"
DISCLAIMER = "Khuyến nghị tham khảo, không thay thế quyết định của cố vấn và nhà trường"


def _active_plan(student_id: str) -> ImprovementPlan | None:
    return db.session.scalar(
        select(ImprovementPlan).where(
            ImprovementPlan.student_id == student_id, ImprovementPlan.status == ACTIVE
        )
    )


def _active_rules(student_id: str) -> list[dict]:
    return [
        {"rule_code": code, "level": level}
        for code, level in m11_public.get_risk_levels(student_id)
        if level in ACTIVE_LEVELS
    ]


def _item_json(item: ImprovementPlanItem) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "due_date": item.due_date.isoformat() if item.due_date else None,
        "done": item.done_at is not None,
        "order": item.order,
    }


def _items(plan_id: str) -> list[ImprovementPlanItem]:
    return list(
        db.session.scalars(
            select(ImprovementPlanItem)
            .where(ImprovementPlanItem.plan_id == plan_id)
            .order_by(ImprovementPlanItem.order, ImprovementPlanItem.id)
        )
    )


def describe(student: Student) -> dict:
    plan = _active_plan(student.id)
    rules = _active_rules(student.id)
    known = set(plan.source_rule_codes) if plan else set()
    return {
        "student_id": student.id,
        "active_rules": rules,
        "new_rules": [rule["rule_code"] for rule in rules if rule["rule_code"] not in known],
        "disclaimer": DISCLAIMER,
        "plan": (
            {
                "id": plan.id,
                "title": plan.title,
                "source_rule_codes": plan.source_rule_codes,
                "created_at": iso_time(plan.created_at),
                "items": [_item_json(item) for item in _items(plan.id)],
            }
            if plan
            else None
        ),
    }


def _add_from_templates(plan: ImprovementPlan, rule_codes: list[str], start: int) -> None:
    templates = db.session.scalars(
        select(RiskActionTemplate)
        .where(RiskActionTemplate.rule_code.in_(rule_codes))
        .order_by(RiskActionTemplate.order)
    ).all()
    order = start
    for code in rule_codes:
        for template in templates:
            if template.rule_code == code:
                order += 1
                db.session.add(
                    ImprovementPlanItem(
                        plan_id=plan.id, title=template.title, order=order, is_mock=True
                    )
                )
    db.session.flush()


def create_plan(student: Student) -> None:
    if _active_plan(student.id) is not None:
        raise ApiError(409, message="Bạn đã có kế hoạch cải thiện.", code="PLAN_EXISTS")
    codes = [rule["rule_code"] for rule in _active_rules(student.id)]
    if not codes:
        raise ApiError(
            422, message="Không có quy tắc nào ở mức theo dõi hoặc cảnh báo.", code="NO_ACTIVE_RISK"
        )
    plan = ImprovementPlan(
        student_id=student.id,
        title=TITLE,
        source_rule_codes=codes,
        status=ACTIVE,
        created_at=clock.utcnow(),
        is_mock=True,
    )
    db.session.add(plan)
    db.session.flush()
    _add_from_templates(plan, codes, 0)


def _owned_plan(student: Student, plan_id: str) -> ImprovementPlan:
    plan = db.session.get(ImprovementPlan, plan_id)
    if plan is None or plan.student_id != student.id:
        raise ApiError(404)
    return plan


def _last_order(plan_id: str) -> int:
    return (
        db.session.scalar(
            select(func.max(ImprovementPlanItem.order)).where(
                ImprovementPlanItem.plan_id == plan_id
            )
        )
        or 0
    )


def add_new_risks(student: Student, plan_id: str) -> None:
    """Chỉ thêm mục cho rủi ro mới, không đụng mục sinh viên đã sửa (Q107)."""
    plan = _owned_plan(student, plan_id)
    known = set(plan.source_rule_codes)
    fresh = [r["rule_code"] for r in _active_rules(student.id) if r["rule_code"] not in known]
    if not fresh:
        raise ApiError(409, message="Không có rủi ro mới.", code="NO_NEW_RISK")
    _add_from_templates(plan, fresh, _last_order(plan.id))
    plan.source_rule_codes = [*plan.source_rule_codes, *fresh]
    db.session.flush()


def add_item(student: Student, plan_id: str, payload: dict) -> None:
    plan = _owned_plan(student, plan_id)
    db.session.add(
        ImprovementPlanItem(
            plan_id=plan.id,
            title=payload["title"].strip(),
            due_date=payload.get("due_date"),
            order=_last_order(plan.id) + 1,
            is_mock=True,
        )
    )
    db.session.flush()


def _owned_item(student: Student, plan_id: str, item_id: str) -> ImprovementPlanItem:
    plan = _owned_plan(student, plan_id)
    item = db.session.get(ImprovementPlanItem, item_id)
    if item is None or item.plan_id != plan.id:
        raise ApiError(404)
    return item


def update_item(student: Student, plan_id: str, item_id: str, payload: dict) -> None:
    item = _owned_item(student, plan_id, item_id)
    if "title" in payload:
        item.title = payload["title"].strip()
    if "due_date" in payload:
        item.due_date = payload["due_date"]
    if "done" in payload:
        item.done_at = clock.utcnow() if payload["done"] else None
    db.session.flush()


def delete_item(student: Student, plan_id: str, item_id: str) -> None:
    db.session.delete(_owned_item(student, plan_id, item_id))
    db.session.flush()
