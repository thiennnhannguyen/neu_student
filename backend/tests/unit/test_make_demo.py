"""Phản hồi CR-11 (B4): `make demo` = seed-demo + dev ở đúng ngày demo của dữ liệu LMS mẫu."""

import re
from pathlib import Path

from scripts import demo_k68_content as content

MAKEFILE = Path(__file__).resolve().parents[3] / "Makefile"


def test_make_demo_seeds_then_runs_dev_on_the_demo_date():
    text = MAKEFILE.read_text(encoding="utf8")
    assert re.search(r"^DEMO_DATE \?= (\S+)$", text, re.M).group(1) == content.LMS_DEMO_TODAY
    recipe = re.search(r"^demo: seed-demo\n((?:\t.*\n)+)", text, re.M)
    assert recipe is not None
    assert recipe.group(1).strip() == "DEMO_TODAY=$(DEMO_DATE) $(MAKE) dev"
