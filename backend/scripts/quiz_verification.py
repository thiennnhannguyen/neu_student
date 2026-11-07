"""Sinh docs/QUIZ_VERIFICATION.md: câu nào đã chạy thật, câu nào chỉ dựa trên lý thuyết."""

from pathlib import Path

from scripts.backend_modules import MODULES

OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "QUIZ_VERIFICATION.md"


def render() -> str:
    lines = [
        "# Kiểm chứng ngân hàng câu hỏi",
        "",
        "Sinh bằng `python -m scripts.quiz_verification`. Câu **đã chạy** có test thật cùng khóa ở "
        "`backend/tests/content/test_quiz_checks.py`. Câu **lý thuyết** không chạy được hoặc chỉ "
        "theo quy ước, quản lý dự án rà tay. Câu hỏi do nhóm biên soạn.",
        "",
        "| Mô-đun | Tổng | Đã chạy | Lý thuyết |",
        "|--------|------|---------|-----------|",
    ]
    for module in MODULES:
        run = sum(q["check"] == "run" for q in module["questions"])
        total = len(module["questions"])
        lines.append(f"| {module['order']}. {module['title']} | {total} | {run} | {total - run} |")
    questions = [q for module in MODULES for q in module["questions"]]
    run = sum(q["check"] == "run" for q in questions)
    lines += [f"| **Tổng** | {len(questions)} | {run} | {len(questions) - run} |", ""]
    for module in MODULES:
        lines += [f"## Mô-đun {module['order']}. {module['title']}", ""]
        lines += [
            "| Khóa | Loại | Kiểm chứng | Câu hỏi |",
            "|------|------|------------|---------|",
        ]
        for number, question in enumerate(module["questions"], start=1):
            state = "đã chạy" if question["check"] == "run" else "lý thuyết"
            prompt = question["prompt"].replace("|", "\\|")
            key = f"m{module['order']}q{number:02d}"
            lines.append(f"| {key} | {question['kind']} | {state} | {prompt} |")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf8")
