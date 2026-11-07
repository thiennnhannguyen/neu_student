# ruff: noqa: E501
"""Sinh fixture profile demo-k68 và docs/DATA_K68.md từ 2 tài liệu trong docs/spec/.

Chạy: .venv/bin/python -m scripts.build_demo_k68. Test chạy lại hàm build() và so với file đã commit.
"""

import base64
import hashlib
import html
import json
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from app.common.text import normalize_name
from scripts import backend_modules as modules
from scripts import demo_k68_content as content
from scripts import khmt_official as official

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
SPEC = ROOT / "docs" / "spec"
OUT = BACKEND / "app" / "seed" / "fixtures_demo_k68"
TEST_FIXTURES = BACKEND / "app" / "seed" / "fixtures"
DOC = ROOT / "docs" / "DATA_K68.md"
OFFICIAL_DOC = ROOT / "docs" / "DATA_OFFICIAL.md"
PROGRAM_BY_SECTION = {"1": "CNTT", "2": "KTPM", "3": "KHMT", "4": "ATTT"}
PUBLISHED_AT = "2026-11-07T08:00:00"
APPROVED_AT = "2026-11-07T07:00:00"
NO_CODE_ID = "EP17.SONGSONG"
PARALLEL_NAME = "Lập trình song song và phân tán"
CODE_FIXES = {"EP17.CNTT1112": "EP17.CNTT11112", "EP17.CNTT1113": "EP17.CNTT11113"}
LANGUAGE = re.compile(r"NNKC")
GROUPS = {
    "1": ("group-chung", "chung", "Học phần chung"),
    "2": ("group-truong", "truong", "Học phần của trường"),
    "3": ("group-nen-tang", "nen-tang", "Học phần nền tảng ngành"),
    "4": ("group-co-so", "co-so", "Cơ sở ngành"),
    "5": ("group-nganh", "nganh", "Kiến thức ngành"),
    "6": ("group-tu-chon", "tu-chon", "Học phần tự chọn"),
    "extra": ("group-tu-chon", "tu-chon", "Học phần riêng bổ sung của EP17"),
    "thesis": ("group-khoa-luan", "khoa-luan", "Khóa luận tốt nghiệp"),
}
# Mã thuộc nhiều nhóm giữa các ngành: lấy nhóm không phải tự chọn.
GROUP_RANK = {"1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "thesis": 5, "6": 6, "extra": 7}


def fixed_code(program: str, row_name: str, code: str) -> str:
    """Mã đúng của một dòng cẩm nang: 2 môn kinh tế theo tên (PDF), KHMT theo mã trong PDF."""
    plain = official.ECONOMICS_CODE_BY_NAME.get(row_name)
    if plain:
        return f"EP17.{plain}" if program == "KTPM" else plain
    return official.K68_TO_OFFICIAL.get(code, code) if program == "KHMT" else code


def modules_career_key() -> str:
    return "backend"


def module_row_id(order: int) -> str:
    return f"module-backend-khmt-{order}"


def module_skill_id(order: int) -> str:
    return f"sk-backend-khmt-m{order}"


def version_id_of(program: str) -> str:
    return official.VERSION_ID if program == "KHMT" else f"pv-{program.lower()}-k68"


@dataclass
class Row:
    number: int
    name: str
    priority_label: str
    purpose: str
    codes: dict[str, tuple[str, str, int | None]]
    stage: int = 0
    mentioned: bool = True
    reason: str = ""


@dataclass
class Stage:
    number: int
    name: str
    contents: str
    deliverable: str


@dataclass
class CareerSource:
    number: str
    group: str
    orientation: str
    objective: str
    rows: list[Row]
    stages: list[Stage]
    self_study: list[str]
    projects: list[tuple[str, str, str]]
    checklist: list[str]


@dataclass
class Report:
    placed: list[tuple[str, str, int, str]] = field(default_factory=list)
    merged: list[tuple[str, str, str, str]] = field(default_factory=list)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf8")


def parse_curriculum(text: str) -> dict[str, list[tuple[str, str, str]]]:
    """Trả {ngành: [(mã, tên, nhóm)]} đúng nguyên văn tài liệu CTĐT."""
    result: dict[str, list[tuple[str, str, str]]] = {}
    program = group = None
    for line in text.splitlines():
        if match := re.match(r"# (\d)\. ", line):
            program = PROGRAM_BY_SECTION.get(match[1])
            if program:
                result[program] = []
        elif line.startswith("# "):
            program = None
        elif program is None:
            continue
        elif match := re.match(r"## \d\.(\d)\. ", line):
            group = match[1]
        elif match := re.match(r"\| \d+\s+\| (.*?)\s+\| (\S+)\s+\|", line):
            result[program].append((match[2], match[1], group))
        elif line.startswith("Học phần riêng bổ sung"):
            for name, code in re.findall(r"([^:;]+?) — (\S+) \(3 tín chỉ\)", line):
                result[program].append((code, name.strip(), "extra"))
        elif match := re.match(
            r"Khóa luận tốt nghiệp \(10 tín chỉ\): (.*?) — Mã học phần: (\S+?)\.$", line
        ):
            result[program].append((match[2], match[1], "thesis"))
    return result


def _codes(cell: str) -> dict[str, tuple[str, str, int | None]]:
    codes = {}
    for line in re.split(r"<br />\s*", cell):
        match = re.match(
            r"\s*(CNTT|KTPM|KHMT|ATTT): (\S+) \((BB|TC)(?:, HK (\d+)|, chưa ghi HK)?\)\s*$",
            html.unescape(line),
        )
        if match is None:
            raise ValueError(f"Không đọc được dòng mã: {line!r}")
        codes[match[1]] = (match[2], match[3], int(match[4]) if match[4] else None)
    return codes


def _table_rows(section: str) -> list[list[str]]:
    rows = []
    for line in section.splitlines():
        if line.startswith("|") and not line.startswith("|--") and "**" not in line:
            rows.append([cell.strip().replace("\\.", ".") for cell in line.strip("|").split(" | ")])
    return rows


def _between(body: str, start: str, end: str) -> str:
    return body.split(start, 1)[1].split(end, 1)[0]


def _clean_item(text: str) -> str:
    text = text.strip().rstrip(".")
    return text[0].upper() + text[1:]


def parse_handbook(text: str) -> list[CareerSource]:
    parts = re.split(r"\n# (\d\d)\. ", text)
    careers = []
    for index in range(1, len(parts), 2):
        number, body = parts[index], parts[index + 1].split("PHẦN II")[0]
        rows = [
            Row(
                int(row[0]),
                html.unescape(row[1]),
                row[2],
                html.unescape(row[4]),
                _codes(row[3]),
            )
            for row in re.findall(
                r"<td>(\d+)\. (.*?)<br />\s*\[(.*?)\]</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>",
                body,
                re.S,
            )
        ]
        stages = [
            Stage(int(cells[0].split(".")[0]), cells[0].split(". ", 1)[1], cells[1], cells[2])
            for cells in _table_rows(_between(body, "## B.", "## C."))
        ]
        study = _between(body, "## C.", "## D.").split("\n\n")[1]
        careers.append(
            CareerSource(
                number=number,
                group=re.search(r"\*\*Nhóm nghề: (.*?)\*\*", body)[1],
                orientation=re.search(r"Định hướng ngành: (.*)", body)[1].strip(),
                objective=re.search(r"Mục tiêu đầu ra: (.*)", body)[1].strip(),
                rows=rows,
                stages=stages,
                self_study=[
                    item.strip().rstrip(".") for item in re.split(r", |; ", study) if item.strip()
                ],
                projects=[
                    (cells[0], cells[1], cells[2])
                    for cells in _table_rows(_between(body, "## D.", "## E."))
                ],
                checklist=[
                    _clean_item(item) for item in body.split("## E.")[1].split("\n\n")[1].split(";")
                ],
            )
        )
    return careers


def assign_stages(career: CareerSource, report: Report) -> None:
    """Giai đoạn sớm nhất có nhắc tới môn. Không nhắc thì lấy nơi đặt và lý do viết tay."""
    for row in career.rows:
        aliases = content.STAGE_ALIASES.get(row.name, [row.name])
        stage = next(
            (
                item.number
                for item in career.stages
                if any(alias.casefold() in item.contents.casefold() for alias in aliases)
            ),
            None,
        )
        manual = content.UNMENTIONED.get((career.number, row.name))
        if (stage is None) != (manual is not None):
            raise ValueError(f"Nơi đặt môn không khớp: {career.number} {row.name}")
        if manual:
            row.stage, row.reason = manual
            row.mentioned = False
            report.placed.append((career.number, row.name, *manual))
        else:
            row.stage = stage


def _row(table: list, **values) -> None:
    table.append({**values, "is_mock": True})


class Builder:
    def __init__(self):
        self.curriculum = parse_curriculum(_text(SPEC / "ctdt-k68-2026.md"))
        self.k68_khmt = self.curriculum.pop("KHMT")
        self.careers = parse_handbook(_text(SPEC / "lo-trinh-10-nghe-k68.md"))
        self.report = Report()
        self.tables: dict[str, list[dict]] = {}
        for career in self.careers:
            assign_stages(career, self.report)
        # (ngành, mã đúng) -> (loại BB/TC, học kỳ) theo cẩm nang.
        self.planned: dict[tuple[str, str], tuple[str, int | None]] = {}
        self._k68_planned: dict[str, int | None] = {}
        for career in self.careers:
            for row in career.rows:
                for program, (code, kind, semester) in row.codes.items():
                    self.planned[(program, fixed_code(program, row.name, code))] = (kind, semester)
                    if program == "KHMT":
                        self._k68_planned[code] = semester

    def _entries(self, program: str) -> list[tuple[str, str | None, str, str]]:
        """(id, mã, tên, nhóm). Mã đã sửa theo cẩm nang; môn trùng mã thì mã rỗng (Q94)."""
        if program == "KHMT":
            return [
                (row[0], row[1], row[6] or row[2], official.GROUPS[row[5]][0])
                for row in official.ROWS
            ]
        entries = []
        for code, name, group in self.curriculum[program]:
            plain = code.removeprefix("EP17.")
            name = official.ECONOMICS_NAME_BY_CODE.get(plain, name)
            if code == "EP17.CNTT1107" and name == PARALLEL_NAME:
                entries.append((NO_CODE_ID, None, name, group))
            else:
                fixed = CODE_FIXES.get(code, code)
                entries.append((fixed, fixed, name, group))
        return entries

    def build_courses(self) -> None:
        groups: dict[str, str] = {}
        names: dict[str, tuple[str | None, str]] = {}
        for program in content.PROGRAM_ORDER:
            for course_id, code, name, group in self._entries(program):
                names.setdefault(course_id, (code, name))
                if course_id not in groups or GROUP_RANK[group] < GROUP_RANK[groups[course_id]]:
                    groups[course_id] = group
        group_rows, course_rows = [], []
        for _id, slug, name in {GROUPS[key][0]: GROUPS[key] for key in GROUPS}.values():
            _row(group_rows, id=_id, slug=slug, name=name)
        pdf = {row[0]: row for row in official.ROWS}
        for course_id in sorted(names):
            code, name = names[course_id]
            credits = 10 if groups[course_id] == "thesis" else 3
            if course_id in pdf:
                name, credits = pdf[course_id][2], pdf[course_id][3]
            credits = official.SHARED_CREDITS.get(course_id, credits)
            _row(
                course_rows,
                id=course_id,
                code=code,
                name=name,
                credits=credits,
                counts_gpa=True,
                course_group_id=GROUPS[groups[course_id]][0],
                short_desc=None,
            )
        for course_id, code, name, credits in official.NOT_COUNTED:
            _row(
                course_rows,
                id=course_id,
                code=code,
                name=name,
                credits=credits,
                counts_gpa=False,
                course_group_id=GROUPS["1"][0],
                short_desc=None,
            )
        self.tables["course_groups"] = group_rows
        self.tables["courses"] = course_rows
        self.course_names = {course_id: value[1] for course_id, value in names.items()}

    def build_programs(self) -> None:
        programs, versions, electives, requirements = [], [], [], []
        for program in content.PROGRAM_ORDER:
            program_id, name, degree = content.PROGRAMS[program]
            version_id = version_id_of(program)
            elective_id = f"eg-{version_id}"
            _row(programs, id=program_id, name=name, code=program, degree_code=degree)
            if program == "KHMT":
                self._official_program(program_id, name, versions, electives, requirements)
                continue
            _row(
                versions,
                id=version_id,
                program_id=program_id,
                version=1,
                effective_cohort="K68",
                name=f"CTĐT {name} K68 – 2026",
                note=content.PROGRAM_NOTE,
                applies_to_cohorts=["K66", "K67"],
            )
            _row(
                electives,
                id=elective_id,
                program_version_id=version_id,
                name="Tự chọn: chọn 10 học phần (30 tín chỉ)",
                min_credits=30,
            )
            for course_id, code, name, group in self._entries(program):
                kind, semester = self.planned.get((program, course_id), (None, None))
                required = group not in ("6", "extra") if kind is None else kind == "BB"
                _row(
                    requirements,
                    id=f"cr-{version_id}-{course_id}",
                    program_version_id=version_id,
                    course_id=course_id,
                    requirement_type="required" if required else "elective",
                    elective_group_id=None if required else elective_id,
                    planned_semester=semester,
                    curriculum_group=GROUPS[group][2],
                    data_warning=self._warning(program, course_id, code),
                    schedule_role=_schedule_role(name),
                )
        self.tables["programs"] = programs
        self.tables["program_versions"] = versions
        self.tables["elective_groups"] = electives
        self.tables["curriculum_requirements"] = requirements

    @staticmethod
    def _official_program(program_id, name, versions, electives, requirements) -> None:
        version_id = official.VERSION_ID
        _row(
            versions,
            id=version_id,
            program_id=program_id,
            version=1,
            effective_cohort="K66",
            name=f"CTĐT {name} – áp dụng từ K66",
            note=official.NOTE,
            applies_to_cohorts=["K67"],
        )
        for key, (group_name, credits) in official.ELECTIVE_GROUPS.items():
            _row(
                electives,
                id=f"eg-{version_id}-{key}",
                program_version_id=version_id,
                name=group_name,
                min_credits=credits,
            )
        for course_id, _code, _name, _credits, semester, group, _old in official.ROWS:
            _key, label, kind, elective, _total = official.GROUPS[group]
            _row(
                requirements,
                id=f"cr-{version_id}-{course_id}",
                program_version_id=version_id,
                course_id=course_id,
                requirement_type=kind,
                elective_group_id=f"eg-{version_id}-{elective}" if elective else None,
                planned_semester=semester,
                curriculum_group=label,
                data_warning=official.warning(course_id),
                # PDF ghi học kỳ của Chuyên đề thực tế nên không cần vị trí giả định (Q99).
                schedule_role="thesis" if group == "khoa-luan" else None,
            )

    @staticmethod
    def _warning(program: str, course_id: str, code: str | None) -> str | None:
        if program == "KTPM" and course_id in ("EP17.KHMA1101", "EP17.KHMI1101"):
            return content.WARN_SWAP
        if program == "ATTT" and course_id in ("KHMA1101", "KHMI1101"):
            return content.WARN_ATTT
        if code is None:
            return content.WARN_NO_CODE
        if course_id == "EP17.CNTT1107":
            return content.WARN_DUP
        if LANGUAGE.search(course_id):
            return content.WARN_LANGUAGE
        for old, new in CODE_FIXES.items():
            if course_id == new:
                return content.WARN_CODE.format(old=old, new=new)
        return None

    def _codes_by_name(self, program: str) -> dict[str, str]:
        return {name: course_id for course_id, _c, name, _g in self._entries(program)}

    def build_prerequisites(self) -> None:
        pairs: dict[tuple[str, str], None] = {}
        for program in content.PROGRAM_ORDER:
            codes = self._codes_by_name(program)
            for befores, afters in content.PEDAGOGICAL_ORDER:
                for before in befores:
                    for after in afters:
                        if before in codes and after in codes and codes[before] != codes[after]:
                            pairs[(codes[after], codes[before])] = None
        rows = []
        for course_id, before_id in sorted(pairs):
            _row(
                rows,
                id=f"pre-{course_id}-{before_id}",
                course_id=course_id,
                prerequisite_course_id=before_id,
                kind="recommended_order",
                source=content.SOURCE_ORDER,
            )
        self.tables["course_prerequisites"] = rows

    def build_equivalencies(self) -> None:
        """Chỉ cặp EP17.X và X cùng tên (không phân biệt hoa thường, Q96)."""
        rows, scopes = [], []
        names = self.course_names
        versions = {program: version_id_of(program) for program in content.PROGRAM_ORDER}
        members = {
            program: {course_id for course_id, *_rest in self._entries(program)}
            for program in content.PROGRAM_ORDER
        }
        for course_id in sorted(names):
            plain = course_id.removeprefix("EP17.")
            if plain == course_id or plain not in names:
                continue
            if names[course_id].casefold() != names[plain].casefold():
                continue
            equivalency_id = f"eq-{plain}"
            _row(
                rows,
                id=equivalency_id,
                course_a_id=course_id,
                course_b_id=plain,
                status="approved",
                source=content.SOURCE_EQUIVALENCY,
                approved_by="user-admin",
                approved_at=APPROVED_AT,
            )
            for program in content.PROGRAM_ORDER:
                if course_id in members[program] or plain in members[program]:
                    _row(
                        scopes,
                        id=f"eqs-{equivalency_id}-{program.lower()}",
                        equivalency_id=equivalency_id,
                        program_version_id=versions[program],
                    )
        self.tables["course_equivalencies"] = rows
        self.tables["course_equivalency_scopes"] = scopes

    def _course_rows(self, career: CareerSource, key: str, version_id: str) -> list[dict]:
        rows: list[dict] = []
        for program in content.PROGRAM_ORDER:
            used: dict[str, dict] = {}
            for row in sorted(career.rows, key=lambda item: (item.stage, item.number)):
                if program not in row.codes:
                    continue
                code = fixed_code(program, row.name, row.codes[program][0])
                subject = f"{key}-{row.number:02d}"
                if code in used:
                    used[code]["also_covers"].append(subject)
                    self.report.merged.append(
                        (career.number, program, code, f"{used[code]['subject_name']} + {row.name}")
                    )
                    continue
                entry = {
                    "id": f"req-k68-{key}-{row.number:02d}-{program}",
                    "career_version_id": version_id,
                    "career_node_id": f"node-k68-{key}-{row.stage}",
                    "kind": "course",
                    "course_id": code,
                    "skill_id": None,
                    "weight": 1,
                    "source": content.SOURCE_CAREER,
                    "status": "approved",
                    "approved_by": "user-admin",
                    "approved_at": APPROVED_AT,
                    "program_id": content.PROGRAMS[program][0],
                    "subject_key": subject,
                    "subject_name": row.name,
                    "also_covers": [],
                    "priority": content.PRIORITIES[row.priority_label],
                    "purpose": row.purpose,
                    "is_mock": True,
                }
                used[code] = entry
                rows.append(entry)
        for entry in rows:
            entry["also_covers"] = entry["also_covers"] or None
        return rows

    def build_careers(self) -> None:
        careers, versions, nodes, requirements, skills = [], [], [], [], []
        skill_by_key: dict[str, str] = {}

        def skill_id(identifier, name, kind, level=None, criteria=None) -> str:
            name_key = normalize_name(name)
            if name_key not in skill_by_key:
                skill_by_key[name_key] = identifier
                _row(
                    skills,
                    id=identifier,
                    name=name,
                    kind=kind,
                    name_key=name_key,
                    short_desc=None,
                    level=level,
                    criteria=criteria,
                )
            return skill_by_key[name_key]

        def skill_requirement(version_id, key, node, identifier, target, kind, program_id=None):
            _row(
                requirements,
                id=f"req-k68-{key}-{identifier}",
                career_version_id=version_id,
                career_node_id=f"node-k68-{key}-{node}",
                kind=kind,
                course_id=None,
                skill_id=target,
                weight=1,
                source=content.SOURCE_CAREER,
                status="approved",
                approved_by="user-admin",
                approved_at=APPROVED_AT,
                program_id=program_id,
                subject_key=None,
                subject_name=None,
                also_covers=None,
                priority=None,
                purpose=None,
            )

        for order, career in enumerate(self.careers, start=1):
            info = content.CAREERS[career.number]
            key = info["key"]
            note = content.SELF_STUDY_NOTES.get(career.number)
            if note is not None and note not in career.self_study:
                raise ValueError(f"Cẩm nang không còn câu lưu ý: {note}")
            version_id = f"cv-k68-{key}-1"
            _row(
                careers,
                id=f"career-k68-{key}",
                slug=info["slug"],
                name=info["name"],
                field=career.group.split(" – ", 1)[1],
                name_key=normalize_name(info["name"]),
                name_en=info["name_en"],
                career_group=career.group,
                objective=career.objective,
                major_fit={
                    "programs": [
                        {"id": content.PROGRAMS[code][0], "code": code} for code in info["fit"]
                    ],
                    "note": career.orientation,
                },
                self_study=[item for item in career.self_study if item != note],
                self_study_note=note,
                illustration_key=info["illustration"],
                tagline=info["tagline"],
                sort_order=order,
            )
            _row(
                versions,
                id=version_id,
                career_id=f"career-k68-{key}",
                version=1,
                status="published",
                published_at=PUBLISHED_AT,
            )
            for stage in career.stages:
                _row(
                    nodes,
                    id=f"node-k68-{key}-{stage.number}",
                    career_version_id=version_id,
                    name=stage.name,
                    order=stage.number,
                    short_desc=None,
                    deliverable=stage.deliverable,
                )
            requirements.extend(self._course_rows(career, key, version_id))
            for number, item in enumerate(career.checklist, start=1):
                target = skill_id(f"sk-k68-{key}-{number}", item, "skill")
                node = content.SKILL_STAGE_OVERRIDES.get((career.number, item), 5)
                if key != modules_career_key():
                    skill_requirement(version_id, key, node, f"sk{number}", target, "skill")
                    continue
                # Backend với KHMT: 10 mô-đun thay cho 6 kỹ năng này, các ngành khác giữ nguyên.
                for program in content.PROGRAM_ORDER:
                    if program != "KHMT":
                        skill_requirement(
                            version_id,
                            key,
                            node,
                            f"sk{number}-{program}",
                            target,
                            "skill",
                            content.PROGRAMS[program][0],
                        )
            for level, name, criteria in career.projects:
                target = skill_id(f"pj-k68-{key}-{level.lower()}", name, "project", level, criteria)
                skill_requirement(version_id, key, 5, f"pj-{level.lower()}", target, "project")
            if key == modules_career_key():
                for module in modules.MODULES:
                    order = module["order"]
                    target = skill_id(
                        module_skill_id(order),
                        f"Mô-đun {order}: {module['title']}",
                        "skill",
                        None,
                        "Đạt bài kiểm tra mô-đun",
                    )
                    skill_requirement(
                        version_id,
                        key,
                        modules.MODULE_STAGE[order],
                        f"m{order}",
                        target,
                        "skill",
                        content.PROGRAMS["KHMT"][0],
                    )
        self.tables["careers"] = careers
        self.tables["career_versions"] = versions
        self.tables["career_nodes"] = nodes
        self.tables["career_requirements"] = requirements
        self.tables["skills"] = skills

    def build_people(self, shared: dict) -> None:
        users = [dict(row) for row in shared["users"]]
        students, assignments, enrollments, attempts, goals, evidences = [], [], [], [], [], []
        levels = sorted(
            (row for row in shared["grade_scale_levels"] if row["grade_scale_id"] == "gs-k66"),
            key=lambda row: row["min_score"],
        )
        credits = {row["id"]: row["credits"] for row in self.tables["courses"]}
        skills = {row["name"]: row["id"] for row in self.tables["skills"]}
        for index, person in enumerate(content.STUDENTS, start=1):
            student_id = person["id"]
            username = person.get("username", student_id.lower())
            user_id = f"user-{username}"
            _row(
                users,
                id=user_id,
                username=username,
                full_name=person.get("full_name", f"Sinh viên {student_id}"),
                role_id="role-student",
                demo_password="Demo@12345",
            )
            _row(
                students,
                id=student_id,
                user_id=user_id,
                student_code=student_id,
                cohort=person["cohort"],
                program_version_id=version_id_of(person["program"]),
                entry_semester_id=person["entry"],
                contact_email=f"{username}@example.test",
                contact_phone=f"09100000{index:02d}",
            )
            _row(
                assignments,
                id=f"aa-{person['advisor']}-{student_id}",
                advisor_user_id=f"user-{person['advisor']}",
                student_id=student_id,
            )
            tries: dict[str, int] = {}
            for semester, results in person["results"].items():
                for raw_id, score in results.items():
                    course_id = self._student_course(person, raw_id)
                    tries[course_id] = tries.get(course_id, 0) + 1
                    value = Decimal(score)
                    level = [row for row in levels if Decimal(str(row["min_score"])) <= value][-1]
                    enrollment_id = f"enr-{student_id}-{course_id}-{semester}"
                    _row(
                        enrollments,
                        id=enrollment_id,
                        student_id=student_id,
                        course_id=course_id,
                        semester_id=semester,
                        status="final",
                    )
                    _row(
                        attempts,
                        id=f"att-{student_id}-{course_id}-{semester}",
                        enrollment_id=enrollment_id,
                        student_id=student_id,
                        course_id=course_id,
                        semester_id=semester,
                        attempt_no=tries[course_id],
                        credits=credits[course_id],
                        score_10=float(value),
                        letter=level["letter"],
                        grade_4=level["grade_4"],
                        passed=level["passed"],
                    )
            for raw_id in person["in_progress"]:
                course_id = self._student_course(person, raw_id)
                _row(
                    enrollments,
                    id=f"enr-{student_id}-{course_id}-S5",
                    student_id=student_id,
                    course_id=course_id,
                    semester_id="S5",
                    status="in_progress",
                )
            _row(
                goals,
                id=f"goal-{student_id}-{person['goal']}",
                student_id=student_id,
                career_id=f"career-k68-{person['goal']}",
                is_primary=True,
                started_at="2026-09-05T08:00:00",
                ended_at=None,
            )
            for number, (skill, status) in enumerate(person["evidences"], start=1):
                reviewed = status == "approved"
                _row(
                    evidences,
                    id=f"ev-{student_id}-{number}",
                    student_id=student_id,
                    skill_id=skills[skill],
                    description=f"Minh chứng cho: {skill}",
                    link="https://example.test/mau/minh-chung",
                    status=status,
                    reviewed_by=f"user-{person['advisor']}" if reviewed else None,
                    reviewed_at="2026-10-15T08:00:00" if reviewed else None,
                    review_note=None,
                    source="submission",
                )
        self.tables["users"] = users
        self.tables["students"] = students
        self.tables["advisor_assignments"] = assignments
        self.tables["enrollments"] = enrollments
        self.tables["grade_attempts"] = attempts
        self.tables["student_career_goals"] = goals
        self.tables["skill_evidences"] = evidences

    def build_framework(self) -> None:
        version_id = f"cv-k68-{modules_career_key()}-1"
        program_id = content.PROGRAMS["KHMT"][0]
        tables = {
            name: []
            for name in (
                "career_modules",
                "career_module_courses",
                "career_milestones",
                "career_milestone_modules",
                "career_suggested_electives",
                "quiz_questions",
                "quiz_options",
                "quiz_attempts",
                "quiz_attempt_questions",
                "certificates",
            )
        }
        for module in modules.MODULES:
            order = module["order"]
            module_id = module_row_id(order)
            _row(
                tables["career_modules"],
                id=module_id,
                career_version_id=version_id,
                program_id=program_id,
                order=order,
                title=module["title"],
                objectives=module["objectives"],
                extra_knowledge=module["extra"],
                practice=module["practice"],
                skill_id=module_skill_id(order),
            )
            for position, (course_id, takeaways) in enumerate(module["courses"].items(), start=1):
                _row(
                    tables["career_module_courses"],
                    id=f"{module_id}-{course_id}",
                    module_id=module_id,
                    course_id=course_id,
                    order=position,
                    takeaways=takeaways,
                )
            for number, question in enumerate(module["questions"], start=1):
                question_id = f"q-m{order}-{number:02d}"
                _row(
                    tables["quiz_questions"],
                    id=question_id,
                    module_id=module_id,
                    order=number,
                    kind=question["kind"],
                    prompt=question["prompt"],
                    code_snippet=question["code"],
                    explanation=question["explanation"],
                    status="approved",
                    verification=question["check"],
                    approved_by="user-admin",
                    approved_at=APPROVED_AT,
                )
                for index, text in enumerate(question["options"]):
                    marked = text.startswith("**") and text.endswith("**")
                    if marked != (index in question["answers"]):
                        raise ValueError(f"Đáp án không khớp: {question_id} {text}")
                    _row(
                        tables["quiz_options"],
                        id=f"{question_id}-{'abcd'[index]}",
                        question_id=question_id,
                        order=index,
                        text=text.strip("*") if marked else text,
                        is_correct=index in question["answers"],
                    )
        for position, (name, members, projects) in enumerate(modules.MILESTONES, start=1):
            milestone_id = f"milestone-backend-khmt-{position}"
            _row(
                tables["career_milestones"],
                id=milestone_id,
                career_version_id=version_id,
                program_id=program_id,
                order=position,
                name=name,
                projects=projects,
            )
            for order in members:
                _row(
                    tables["career_milestone_modules"],
                    id=f"{milestone_id}-m{order}",
                    milestone_id=milestone_id,
                    module_id=module_row_id(order),
                )
        for position, course_id in enumerate(modules.SUGGESTED_ELECTIVES, start=1):
            _row(
                tables["career_suggested_electives"],
                id=f"elective-backend-khmt-{course_id}",
                career_version_id=version_id,
                program_id=program_id,
                course_id=course_id,
                order=position,
            )
        self.tables.update(tables)
        for order, day in ((1, "2026-10-10"), (2, "2026-10-20")):
            self._passed_quiz(order, f"{day}T09:00:00", f"{day}T09:12:00")

    def _passed_quiz(self, order: int, started: str, submitted: str) -> None:
        """thiennhan đạt 9/10 ở mô-đun này: đủ lượt làm bài, chứng chỉ và kỹ năng đạt."""
        student_id = "NEU-KHMT-001"
        module = modules.MODULES[order - 1]
        module_id = module_row_id(order)
        attempt_id = f"att-quiz-{student_id}-m{order}"
        questions = module["questions"][: modules.QUIZ_QUESTION_COUNT]
        _row(
            self.tables["quiz_attempts"],
            id=attempt_id,
            student_id=student_id,
            module_id=module_id,
            attempt_no=1,
            status="submitted",
            started_at=started,
            deadline_at=f"{started[:11]}09:15:00",
            submitted_at=submitted,
            correct_count=len(questions) - 1,
            total=len(questions),
            met_threshold=True,
        )
        for number, question in enumerate(questions, start=1):
            question_id = f"q-m{order}-{number:02d}"
            ids = [f"{question_id}-{'abcd'[i]}" for i in range(len(question["options"]))]
            right = [ids[i] for i in question["answers"]]
            wrong = next(item for item in ids if item not in right)
            is_correct = number != len(questions)
            _row(
                self.tables["quiz_attempt_questions"],
                id=f"{attempt_id}-q{number:02d}",
                attempt_id=attempt_id,
                question_id=question_id,
                order=number,
                option_order=ids,
                selected_option_ids=right if is_correct else [wrong],
                is_correct=is_correct,
            )
        code = base64.urlsafe_b64encode(hashlib.sha256(attempt_id.encode()).digest()[:18]).decode()
        _row(
            self.tables["certificates"],
            id=f"cert-{student_id}-m{order}",
            code=code,
            student_id=student_id,
            module_id=module_id,
            attempt_id=attempt_id,
            student_name="Nguyễn Thiện Nhân",
            module_title=module["title"],
            correct_count=len(questions) - 1,
            total=len(questions),
            issued_at=submitted,
            revoked_at=None,
        )
        _row(
            self.tables["skill_evidences"],
            id=f"ev-{student_id}-quiz-m{order}",
            student_id=student_id,
            skill_id=module_skill_id(order),
            description=f"Đạt bài kiểm tra mô-đun: {module['title']}",
            link=None,
            status="approved",
            reviewed_by=None,
            reviewed_at=submitted,
            review_note=None,
            source="quiz",
        )

    @staticmethod
    def _student_course(person: dict, course_id: str) -> str:
        if person["program"] == "KHMT":
            return official.K68_TO_OFFICIAL.get(course_id, course_id)
        return course_id

    def official_document(self) -> str:
        k68 = {}
        for code, name, group in self.k68_khmt:
            k68[code] = (
                name,
                10 if group == "thesis" else official.SHARED_CREDITS.get(code, 3),
                group,
            )
        for code in ("LLNL1106", "LLNL1107"):
            k68[code] = (k68[code][0], 3, k68[code][2])
        return official.document(k68, {code: self._k68_planned.get(code) for code in k68})

    def build(self) -> dict[str, dict[str, list[dict]]]:
        accounts = json.loads(_text(TEST_FIXTURES / "accounts.json"))
        academic = json.loads(_text(TEST_FIXTURES / "academic.json"))
        semesters = json.loads(_text(TEST_FIXTURES / "semesters.json"))
        plans = json.loads(_text(TEST_FIXTURES / "plans.json"))
        staff = [
            row
            for row in accounts["users"]
            if row["username"] in ("admin", "gv1", "gv2", "ht1", "ht2")
        ]
        self.build_courses()
        self.build_programs()
        self.build_prerequisites()
        self.build_equivalencies()
        self.build_careers()
        self.build_people({"users": staff, "grade_scale_levels": academic["grade_scale_levels"]})
        self.build_framework()
        self.tables["roles"] = accounts["roles"]
        return {
            "academic.json": academic,
            "semesters.json": semesters,
            "plans.json": plans,
            "accounts.json": {
                key: self.tables[key]
                for key in ("roles", "users", "students", "advisor_assignments")
            }
            | {
                # Q104: dùng chung với profile test, giữ nguyên id.
                "support_categories": accounts["support_categories"],
                "support_staff_categories": accounts["support_staff_categories"],
            },
            "courses.json": {
                key: self.tables[key]
                for key in (
                    "course_groups",
                    "courses",
                    "course_prerequisites",
                    "course_equivalencies",
                    "course_equivalency_scopes",
                )
            },
            "programs.json": {
                key: self.tables[key]
                for key in (
                    "programs",
                    "program_versions",
                    "elective_groups",
                    "curriculum_requirements",
                )
            },
            "careers.json": {
                key: self.tables[key]
                for key in (
                    "careers",
                    "career_versions",
                    "career_nodes",
                    "career_requirements",
                    "skills",
                )
            },
            "framework.json": {
                key: self.tables[key]
                for key in (
                    "career_modules",
                    "career_module_courses",
                    "career_milestones",
                    "career_milestone_modules",
                    "career_suggested_electives",
                    "quiz_questions",
                    "quiz_options",
                    "quiz_attempts",
                    "quiz_attempt_questions",
                    "certificates",
                )
            },
            "student_records.json": {
                key: self.tables[key]
                for key in (
                    "enrollments",
                    "grade_attempts",
                    "student_career_goals",
                    "skill_evidences",
                )
            },
        }

    def document(self) -> str:
        lines = [
            "# Dữ liệu demo K68",
            "",
            "Sinh bằng `backend/scripts/build_demo_k68.py` từ `docs/spec/ctdt-k68-2026.md` và "
            "`docs/spec/lo-trinh-10-nghe-k68.md`. Không sửa tay file này.",
            "",
            "Đây là dữ liệu mẫu của nhóm, không phải dữ liệu chính thức của NEU.",
            "",
            "## Giả định của nhóm",
            "",
            "- Tín chỉ của CNTT, KTPM, ATTT: khóa luận 10, còn lại 3, trừ `LLNL1106`, `LLNL1107` là 2. "
            "Mọi môn đều tính vào GPA. KHMT theo PDF, xem `docs/DATA_OFFICIAL.md`.",
            "- Vị trí trong lộ trình (Q99): Khóa luận tốt nghiệp ở kỳ cuối của tầm lộ trình, "
            "Chuyên đề thực tế ưu tiên kỳ ngay trước. Tài liệu nguồn không ghi học kỳ của 2 môn "
            "này, cần xác minh với trường.",
            "- Cẩm nang không có kỹ năng dùng chung giữa các nghề; cơ chế dùng chung được kiểm ở "
            "profile test.",
            f"- CTĐT K68 dùng làm CTĐT mẫu cho sinh viên K66, K67 của CNTT, KTPM, ATTT: “{content.PROGRAM_NOTE}”.",
            f"- Tiên quyết: chỉ dựng từ mục 4 cẩm nang, nguồn “{content.SOURCE_ORDER}”. "
            "M11 không dùng các cạnh này để chặn đăng ký.",
            "- “Security” trong mục 4 là An toàn và bảo mật thông tin, Mật mã và bảo mật thông tin; "
            "“Cloud” là Điện toán đám mây; “CI/CD” là Tích hợp và triển khai phần mềm.",
            f"- Tương đương: chỉ cặp EP17.X và X cùng tên, nguồn “{content.SOURCE_EQUIVALENCY}”. "
            "So tên không phân biệt hoa thường (Thiết kế và lập trình WEB / web).",
            "- Môn CTĐT không có trong cẩm nang: học kỳ rỗng, BB/TC theo nhóm ở tài liệu CTĐT. "
            "EP17.TIHT1123 là TC.",
            "- Nhóm môn chung lấy theo tài liệu CTĐT; mã thuộc 2 nhóm lấy nhóm không phải tự chọn. "
            "Nhóm đúng theo ngành nằm ở `curriculum_requirements.curriculum_group`.",
            "- Khóa học: sinh viên đã học 4 kỳ là K66 (S1–S4), đã học 2 kỳ là K67 (S3–S4), "
            "cả hai đang học S5.",
            "",
            "## Khác biệt giữa 2 tài liệu và dữ liệu cần xác minh",
            "",
            "| Mã | Nội dung | Cách xử lý |",
            "|----|----------|------------|",
            "| EP17.CNTT1112 → EP17.CNTT11112 | Tích hợp và triển khai phần mềm: tài liệu CTĐT ghi "
            "4 chữ số, cẩm nang ghi 5 | Dùng theo cẩm nang |",
            "| EP17.CNTT1113 → EP17.CNTT11113 | Tương tác người máy: như trên | Dùng theo cẩm nang |",
            "| EP17.CNTT1107 | Tài liệu CTĐT ghi cho cả Hệ điều hành và Lập trình song song và phân "
            "tán | Hệ điều hành giữ mã; môn còn lại để mã rỗng, kèm cảnh báo (Q94) |",
            "| KHMA1101, KHMI1101, kể cả mã EP17 | Tài liệu K68 và cẩm nang đảo so với PDF | Theo PDF: "
            "KHMI1101 là vi mô, KHMA1101 là vĩ mô; học kỳ đi theo tên môn |",
            "| KHMA1101, KHMI1101 (ATTT) | Ảnh ATTT ghi hai dòng cùng tên “Kinh tế vi mô 1” (Phần "
            "III mục 4); học kỳ không ghi | Học kỳ rỗng, kèm cảnh báo |",
            "| NNKC1131–1133, EP17.NNKC1168–1170 | Học kỳ Ngoại ngữ/Tiếng Anh không ghi | Học kỳ "
            "rỗng, không tự điền, kèm cảnh báo |",
            "| Thiết kế Web, Lập trình Web (KTPM, ATTT) | Hai dòng cẩm nang cùng 1 mã | Gộp thành 1 "
            "yêu cầu ở giai đoạn sớm hơn, xem bảng dưới |",
            "| Nên học, Tùy chọn | Cẩm nang có 6 mức ưu tiên | Gộp vào `recommended`, nhãn “Nên "
            "chọn” (Q93) |",
            "",
            "## Môn không được nhắc trong lộ trình",
            "",
            "| Nghề | Môn | Giai đoạn | Lý do |",
            "|------|-----|-----------|-------|",
        ]
        for number, name, stage, reason in self.report.placed:
            title = content.CAREERS[number]["name_en"]
            lines.append(f"| {title} | {name} | {stage} | {reason} |")
        lines += [
            "",
            "## Hai dòng cẩm nang cùng 1 mã",
            "",
            "| Nghề | Ngành | Mã | Hai dòng |",
            "|------|-------|----|----------|",
        ]
        for number, program, code, rows in self.report.merged:
            title = content.CAREERS[number]["name_en"]
            lines.append(f"| {title} | {program} | {code} | {rows} |")
        lines += [
            "",
            "## Số môn tính tiến độ theo ngành",
            "",
            "Môn không có trong CTĐT ngành không vào mẫu số (Q92). Độ phủ = số môn có trong CTĐT "
            "ngành / tổng số môn riêng biệt của nghề theo góc nhìn ngành đó (dòng gộp tính 1 lần).",
            "",
            "| Nghề | CNTT | KTPM | KHMT | ATTT |",
            "|------|------|------|------|------|",
        ]
        for career in self.careers:
            cells = []
            for program in content.PROGRAM_ORDER:
                codes = {
                    fixed_code(program, row.name, row.codes[program][0])
                    for row in career.rows
                    if program in row.codes
                }
                missing = sum(program not in row.codes for row in career.rows)
                cells.append(f"{len(codes)}/{len(codes) + missing}")
            title = content.CAREERS[career.number]["name_en"]
            lines.append(f"| {title} | {' | '.join(cells)} |")
        lines += [
            "",
            "## Tính tay % và độ phủ của 4 sinh viên",
            "",
            "Làm tròn half-up từ phân số. Môn đang học không vào tử số; kỹ năng và dự án chỉ tính "
            "minh chứng đã duyệt. Test `tests/acceptance/test_demo_k68.py` so khớp bảng này.",
            "",
        ]
        for item in content.HAND_CALC:
            course, skill, coverage = item["course"], item["skill"], item["coverage"]
            lines += [
                f"### {item['student']} ({item['program']}), nghề {item['career']}",
                "",
                f"- Môn tính: {item['counted']}.",
                f"- Đã đạt: {item['done']}.",
                f"- Không có trong CTĐT ngành: {item['absent']}.",
                f"- Học phần: {course[0]}/{course[1]} = {course[2]}%.",
                f"- Kỹ năng & dự án: {skill[0]}/{skill[1]} = {skill[2]}%.",
                f"- Độ phủ: {coverage[0]}/{coverage[1]} = {coverage[2]}%.",
                "",
            ]
        return "\n".join(lines)


def build() -> tuple[dict[str, dict[str, list[dict]]], str, str]:
    builder = Builder()
    fixtures = builder.build()
    return fixtures, builder.document(), builder.official_document()


def _schedule_role(name: str) -> str | None:
    """Q99: tài liệu nguồn không ghi học kỳ của 2 loại môn này, vị trí là giả định của nhóm."""
    if name.startswith("Khóa luận tốt nghiệp"):
        return "thesis"
    if name.startswith("Chuyên đề thực tế"):
        return "practicum"
    return None


def main() -> None:
    fixtures, document, official_document = build()
    OUT.mkdir(exist_ok=True)
    for name, data in fixtures.items():
        (OUT / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
        )
    DOC.write_text(document, encoding="utf8")
    OFFICIAL_DOC.write_text(official_document, encoding="utf8")


if __name__ == "__main__":
    main()
