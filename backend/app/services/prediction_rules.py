"""Điểm dự kiến, khoảng, độ tin cậy và mức cảnh báo của một môn đang học (CR-13, D-314). Hàm thuần.

Không dùng AI, không đọc DB. Mọi ngưỡng, hệ số lấy từ `settings` (giá trị mẫu ở
prediction_config.DEFAULTS). Tính bằng Decimal với đủ chữ số; chỉ làm tròn 2 chữ số (nửa lên) khi
so ngưỡng và khi trả kết quả, nên test biên (4,49/4,50) đúng như số người dùng thấy.

- Điểm dự kiến = wCC·CC + wQT·QT + wCK·CK.
- CC = 10 − điểm trừ theo số buổi vắng không phép đã xảy ra (D-316, thay "10 × tỷ lệ có mặt" của
  D-314); vắng có phép trừ hay không theo cấu hình (mặc định không, Q90).
- QT = (n × QT hiện tại + k × mức nền) ÷ (n + k); n = số mục đã vào điểm quá trình hiện tại,
  gồm cả bài quá hạn tính 0 (H1), nên thiếu thêm bài không bao giờ làm điểm tăng.
- CK = mức nền + tổng điều chỉnh (giới hạn ±1,5).
- Phần đã biết = 0,5 × buổi đã học ÷ số buổi + wQT × phần trọng số của điểm giữa kỳ đã có.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
TEN = Decimal(10)
ZERO = Decimal(0)

# Mức cảnh báo, từ nặng tới nhẹ; "insufficient" là chưa đủ dữ liệu.
BARRED = "barred"
HIGH = "high"
WATCH = "watch"
OK = "ok"
INSUFFICIENT = "insufficient"
LEVEL_ORDER = (BARRED, HIGH, WATCH, OK, INSUFFICIENT)
SEVERITY = {BARRED: 3, HIGH: 2, WATCH: 1, OK: 0}

CONFIDENCE_LOW = "low"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_HIGH = "high"

UNREACHABLE = "unreachable"
SECURED = "secured"
NEEDED = "needed"

MIDTERM = "midterm"


@dataclass(frozen=True)
class ProcessItem:
    kind: str  # "assignment", "quiz", "midterm"
    score: Decimal
    weight: Decimal


@dataclass(frozen=True)
class ReportPoint:
    week_no: int
    understanding: int
    confidence: int
    self_study: str


@dataclass(frozen=True)
class Baseline:
    value: Decimal
    source: str  # "group", "all", "default"
    courses: int
    group_name: str | None = None


@dataclass(frozen=True)
class Weights:
    attendance: Decimal
    process: Decimal
    final: Decimal


@dataclass(frozen=True)
class CourseInputs:
    total_sessions: int
    attendance: tuple[str, ...]
    process_items: tuple[ProcessItem, ...]
    past_due: int  # bài có hạn trước ngày dữ liệu
    overdue_missing: int  # trong số đó: chưa nộp
    submitted: int  # % hoàn thành = submitted ÷ submit_base (D-309)
    submit_base: int
    reports: tuple[ReportPoint, ...]  # đã nộp, tuần tăng dần
    missed_reports: int
    baseline: Baseline
    weights: Weights
    scale: tuple[tuple[str, Decimal], ...] = ()  # (điểm chữ, điểm tối thiểu)


@dataclass(frozen=True)
class Reason:
    code: str
    level: str
    text: str


@dataclass(frozen=True)
class Adjustment:
    code: str
    value: Decimal
    text: str


@dataclass(frozen=True)
class Target:
    letter: str
    score: Decimal
    status: str
    needed: Decimal | None


@dataclass(frozen=True)
class Prediction:
    level: str
    score: Decimal | None
    letter: str | None
    low: Decimal | None
    high: Decimal | None
    half_width: Decimal | None
    known: Decimal | None
    confidence: str | None
    attendance_score: Decimal | None
    attendance_deduction: Decimal | None
    absent_deduction: Decimal | None
    excused_deduction: Decimal | None
    process_now: Decimal | None
    process_items: int
    process_score: Decimal | None
    final_score: Decimal | None
    adjustments: tuple[Adjustment, ...]
    adjust_total: Decimal
    reasons: tuple[Reason, ...]
    targets: tuple[Target, ...]
    absent: int
    excused: int
    present: int
    held: int


def dec(settings: dict, key: str) -> Decimal:
    return Decimal(str(settings[key]))


def r2(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def vn(value: Decimal) -> str:
    """Số kiểu Việt cho câu lý do: 2 chữ số, dấu phẩy."""
    return str(r2(value)).replace(".", ",")


def weights_for(settings: dict, course_id: str) -> Weights:
    raw = settings["weights"] | settings["course_weights"].get(course_id, {})
    return Weights(*(Decimal(str(raw[key])) for key in ("attendance", "process", "final")))


def weighted_average(items: tuple[ProcessItem, ...]) -> Decimal | None:
    total = sum((item.weight for item in items), ZERO)
    if total == 0:
        return None
    return sum((item.score * item.weight for item in items), ZERO) / total


def letter_of(scale: tuple[tuple[str, Decimal], ...], score: Decimal) -> str | None:
    eligible = [(minimum, letter) for letter, minimum in scale if minimum <= r2(score)]
    return max(eligible)[1] if eligible else None


# --- Chuyên cần ---


def attendance_level(settings: dict, absent: int, excused: int) -> tuple[str, list[Reason]]:
    """D-311, Q88: không phép và có phép tính riêng, lấy mức cao nhất."""
    reasons = []
    for kind, count, label, more in (
        ("absent", absent, "không phép", "vắng thêm"),
        ("excused", excused, "có phép", "vắng có phép thêm"),
    ):
        barred = settings[f"{kind}_barred_from"]
        if count >= barred:
            reasons.append(
                Reason(
                    f"attendance_{kind}",
                    BARRED,
                    f"Vắng {count} buổi {label} – không đủ điều kiện dự thi",
                )
            )
        elif count >= settings[f"{kind}_watch_from"]:
            level = HIGH if count >= settings[f"{kind}_high_from"] else WATCH
            left = barred - count
            reasons.append(
                Reason(
                    f"attendance_{kind}",
                    level,
                    f"Vắng {count} buổi {label} – {more} {left} buổi sẽ không được dự thi",
                )
            )
    return _highest(reasons), reasons


def attendance_deduction(
    settings: dict, absences: int, table_key: str = "attendance_deductions"
) -> Decimal:
    """D-316, D-330: điểm trừ theo số buổi vắng của một loại; vượt bảng thì lấy mức lớn nhất.

    table_key: "attendance_deductions" (không phép) hoặc "excused_deductions" (có phép).
    """
    table = {int(count): Decimal(str(value)) for count, value in settings[table_key].items()}
    return table[min(absences, max(table))]


def _highest(reasons: list[Reason]) -> str:
    return max((reason.level for reason in reasons), key=SEVERITY.get, default=OK)


# --- Điều chỉnh điểm cuối kỳ ---


def _mean(values: list[Decimal]) -> Decimal:
    return sum(values, ZERO) / len(values)


def final_adjustments(settings: dict, inputs: CourseInputs) -> list[Adjustment]:
    items = []
    window = inputs.reports[-settings["report_window"] :]
    if window:
        understanding = _mean([Decimal(point.understanding) for point in window])
        first, last = window[0].understanding, window[-1].understanding
        if understanding >= dec(settings, "understanding_high_from"):
            items.append(
                Adjustment(
                    "understanding_high",
                    dec(settings, "understanding_high_bonus"),
                    f"Mức hiểu bài trung bình {vn(understanding)} ({len(window)} báo cáo gần nhất)",
                )
            )
        elif understanding <= dec(settings, "understanding_low_to"):
            text = (
                f"Mức hiểu bài giảm từ {first} xuống {last}"
                if first > last
                else f"Mức hiểu bài trung bình {vn(understanding)} ({len(window)} báo cáo gần nhất)"
            )
            items.append(
                Adjustment("understanding_low", -dec(settings, "understanding_low_penalty"), text)
            )
        hours = _mean([Decimal(str(settings["self_study_hours"][p.self_study])) for p in window])
        if hours > dec(settings, "self_study_high_above"):
            items.append(
                Adjustment(
                    "self_study_high",
                    dec(settings, "self_study_high_bonus"),
                    f"Tự học khoảng {vn(hours)} giờ/tuần",
                )
            )
        elif hours < dec(settings, "self_study_low_below"):
            items.append(
                Adjustment(
                    "self_study_low",
                    -dec(settings, "self_study_low_penalty"),
                    f"Tự học khoảng {vn(hours)} giờ/tuần",
                )
            )
    if inputs.submit_base:
        rate = Decimal(inputs.submitted) / Decimal(inputs.submit_base)
        text = f"Đã nộp {inputs.submitted}/{inputs.submit_base} bài đến hạn"
        if rate >= dec(settings, "submit_rate_high_from"):
            items.append(
                Adjustment("submit_rate_high", dec(settings, "submit_rate_high_bonus"), text)
            )
        elif rate < dec(settings, "submit_rate_low_below"):
            items.append(
                Adjustment("submit_rate_low", -dec(settings, "submit_rate_low_penalty"), text)
            )
    if inputs.missed_reports >= settings["missed_reports_from"]:
        items.append(
            Adjustment(
                "missed_reports",
                -dec(settings, "missed_reports_penalty"),
                f"Không nộp {inputs.missed_reports} báo cáo tuần",
            )
        )
    count = settings["confidence_drop_reports"]
    recent = [point.confidence for point in inputs.reports[-count:]]
    if len(recent) == count and all(a > b for a, b in zip(recent, recent[1:], strict=False)):
        items.append(
            Adjustment(
                "confidence_drop",
                -dec(settings, "confidence_drop_penalty"),
                f"Mức tự tin giảm {count} báo cáo liên tiếp ({' → '.join(map(str, recent))})",
            )
        )
    return items


# --- Phần đã biết, khoảng, độ tin cậy ---


def known_share(settings: dict, inputs: CourseInputs) -> Decimal:
    """D-314: theo tiến độ thời gian; có điểm giữa kỳ thì cộng phần trọng số của nó trong phần
    Quá trình (wQT × trọng số giữa kỳ ÷ tổng trọng số các mục quá trình). Tối đa 1."""
    held = Decimal(len(inputs.attendance))
    share = dec(settings, "known_time_share") * held / Decimal(inputs.total_sessions)
    total = sum((item.weight for item in inputs.process_items), ZERO)
    midterm = sum((i.weight for i in inputs.process_items if i.kind == MIDTERM), ZERO)
    if total and midterm:
        share += inputs.weights.process * midterm / total
    return min(share, Decimal(1))


def confidence_of(settings: dict, known: Decimal) -> str:
    if known < dec(settings, "confidence_low_below"):
        return CONFIDENCE_LOW
    if known > dec(settings, "confidence_high_above"):
        return CONFIDENCE_HIGH
    return CONFIDENCE_MEDIUM


def targets_for(settings: dict, inputs: CourseInputs, cc: Decimal, qt: Decimal) -> list[Target]:
    """Cuối kỳ cần bao nhiêu để đạt từng mốc: (mốc − wCC·CC − wQT·QT) ÷ wCK."""
    weights = inputs.weights
    if weights.final == 0:
        return []  # Môn không có phần cuối kỳ: không có mốc cần đạt.
    known_part = weights.attendance * cc + weights.process * qt
    items = []
    for letter, raw in settings["targets"].items():
        target = Decimal(str(raw))
        needed = r2((target - known_part) / weights.final)
        if needed > TEN:
            items.append(Target(letter, target, UNREACHABLE, None))
        elif needed <= ZERO:
            items.append(Target(letter, target, SECURED, None))
        else:
            items.append(Target(letter, target, NEEDED, needed))
    return items


# --- Mức cảnh báo ---


def assignment_reasons(settings: dict, inputs: CourseInputs) -> list[Reason]:
    """Phản hồi kế hoạch CR-13 (a): thiếu bài quá hạn hoặc tỷ lệ nộp thấp."""
    missing = inputs.overdue_missing
    rate = Decimal(inputs.submitted) / Decimal(inputs.submit_base) if inputs.submit_base else None
    if missing >= settings["missing_high_from"]:
        return [Reason("assignments_missing", HIGH, _missing_text(inputs))]
    if rate is not None and rate < dec(settings, "rate_high_below"):
        return [Reason("assignments_rate", HIGH, _rate_text(inputs, rate))]
    if missing >= settings["missing_watch_from"]:
        return [Reason("assignments_missing", WATCH, _missing_text(inputs))]
    if rate is not None and rate < dec(settings, "rate_watch_below"):
        return [Reason("assignments_rate", WATCH, _rate_text(inputs, rate))]
    return []


def _missing_text(inputs: CourseInputs) -> str:
    return f"Thiếu {inputs.overdue_missing}/{inputs.past_due} bài đã quá hạn"


def _rate_text(inputs: CourseInputs, rate: Decimal) -> str:
    percent = (rate * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return f"Mới nộp {inputs.submitted}/{inputs.submit_base} bài đến hạn ({percent}%)"


def score_reasons(
    settings: dict,
    inputs: CourseInputs,
    score: Decimal,
    high: Decimal,
    history: tuple[Decimal, ...],
) -> list[Reason]:
    reasons = []
    shown = r2(score)
    if shown < dec(settings, "high_score_below"):
        reasons.append(
            Reason(
                "score_low",
                HIGH,
                f"Điểm dự kiến {vn(shown)} dưới ngưỡng đạt {vn(dec(settings, 'high_score_below'))}",
            )
        )
    elif r2(high) < dec(settings, "high_upper_below"):
        reasons.append(
            Reason(
                "upper_low",
                HIGH,
                f"Cận trên của khoảng dự kiến {vn(high)} dưới "
                f"{vn(dec(settings, 'high_upper_below'))}",
            )
        )
    elif shown < dec(settings, "watch_score_below"):
        reasons.append(
            Reason(
                "score_watch",
                WATCH,
                f"Điểm dự kiến {vn(shown)} dưới {vn(dec(settings, 'watch_score_below'))} (mức C)",
            )
        )
    if inputs.missed_reports >= settings["missed_reports_from"]:
        reasons.append(
            Reason("missed_reports", WATCH, f"Không nộp {inputs.missed_reports} báo cáo tuần")
        )
    weeks = settings["decline_weeks"]
    points = [*history[-weeks:], shown]
    if (
        len(points) == weeks + 1
        and all(a > b for a, b in zip(points, points[1:], strict=False))
        and points[0] - points[-1] >= dec(settings, "decline_min_total")
    ):
        reasons.append(
            Reason(
                "declining",
                WATCH,
                f"Điểm dự kiến giảm {vn(points[0] - points[-1])} qua {weeks} tuần "
                f"({' → '.join(vn(point) for point in points)})",
            )
        )
    return reasons


def _sorted(reasons: list[Reason]) -> tuple[Reason, ...]:
    return tuple(sorted(reasons, key=lambda reason: -SEVERITY[reason.level]))


def _without_score(
    level: str, reasons: list[Reason], absent: int, excused: int, present: int, held: int
) -> Prediction:
    """Chưa đủ dữ liệu, hoặc không đủ điều kiện dự thi: không hiện điểm."""
    return Prediction(
        level=level,
        score=None,
        letter=None,
        low=None,
        high=None,
        half_width=None,
        known=None,
        confidence=None,
        attendance_score=None,
        attendance_deduction=None,
        absent_deduction=None,
        excused_deduction=None,
        process_now=None,
        process_items=0,
        process_score=None,
        final_score=None,
        adjustments=(),
        adjust_total=ZERO,
        reasons=_sorted(reasons),
        targets=(),
        absent=absent,
        excused=excused,
        present=present,
        held=held,
    )


def predict(settings: dict, inputs: CourseInputs, history: tuple[Decimal, ...] = ()) -> Prediction:
    """history: điểm dự kiến (đã làm tròn) của các bản chụp trước, cũ trước."""
    held = len(inputs.attendance)
    absent = inputs.attendance.count("absent")
    excused = inputs.attendance.count("excused")
    present = inputs.attendance.count("present")
    if held == 0:
        return _without_score(INSUFFICIENT, [], absent, excused, present, held)
    attendance, attendance_reasons = attendance_level(settings, absent, excused)
    if attendance == BARRED:
        return _without_score(BARRED, attendance_reasons, absent, excused, present, held)
    weights = inputs.weights
    baseline = inputs.baseline.value
    absent_deduction = attendance_deduction(settings, absent)
    excused_deduction = attendance_deduction(settings, excused, "excused_deductions")
    deduction = absent_deduction + excused_deduction
    cc = max(ZERO, TEN - deduction)
    n = len(inputs.process_items)
    now = weighted_average(inputs.process_items)
    k = dec(settings, "prior_strength")
    qt = baseline if now is None else (Decimal(n) * now + k * baseline) / (Decimal(n) + k)
    adjustments = final_adjustments(settings, inputs)
    limit = dec(settings, "final_adjust_limit")
    total = max(-limit, min(limit, sum((item.value for item in adjustments), ZERO)))
    ck = baseline + total
    score = weights.attendance * cc + weights.process * qt + weights.final * ck
    known = known_share(settings, inputs)
    half = max(dec(settings, "half_width_min"), dec(settings, "half_width_scale") * (1 - known))
    low, high = max(ZERO, score - half), min(TEN, score + half)
    reasons = [
        *attendance_reasons,
        *assignment_reasons(settings, inputs),
        *score_reasons(settings, inputs, score, high, history),
    ]
    return Prediction(
        level=_highest(reasons),
        score=score,
        letter=letter_of(inputs.scale, score),
        low=low,
        high=high,
        half_width=half,
        known=known,
        confidence=confidence_of(settings, known),
        attendance_score=cc,
        attendance_deduction=deduction,
        absent_deduction=absent_deduction,
        excused_deduction=excused_deduction,
        process_now=now,
        process_items=n,
        process_score=qt,
        final_score=ck,
        adjustments=tuple(adjustments),
        adjust_total=total,
        reasons=_sorted(reasons),
        targets=tuple(targets_for(settings, inputs, cc, qt)),
        absent=absent,
        excused=excused,
        present=present,
        held=held,
    )
