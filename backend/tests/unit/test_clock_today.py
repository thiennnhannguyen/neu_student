"""D-309: một hàm "hôm nay" duy nhất; DEMO_TODAY ghi đè cho demo; không gọi date.today() rải rác."""

import re
from datetime import date, datetime
from pathlib import Path

import pytest

from app import create_app
from app.common import clock

APP = Path(__file__).resolve().parents[2] / "app"
DIRECT_CALLS = re.compile(r"\bdate\.today\(|\bdatetime\.(?:now|today|utcnow)\(")


def direct_time_calls(source: str) -> list[str]:
    return DIRECT_CALLS.findall(source)


def test_demo_today_overrides_the_real_date():
    app = create_app("testing")
    app.config["DEMO_TODAY"] = "2026-10-26"
    with app.app_context():
        assert clock.today() == date(2026, 10, 26)


def test_without_demo_today_uses_the_date_in_vietnam(monkeypatch):
    class Fixed(datetime):
        @classmethod
        def now(cls, tz=None):
            # 18:30 UTC ngày 25/10 là 01:30 sáng 26/10 ở Việt Nam.
            return datetime(2026, 10, 25, 18, 30, tzinfo=clock.UTC).astimezone(tz)

    monkeypatch.setattr(clock, "datetime", Fixed)
    app = create_app("testing")
    app.config["DEMO_TODAY"] = None
    with app.app_context():
        assert clock.today() == date(2026, 10, 26)


def test_only_clock_reads_the_system_time():
    problems = {
        str(path.relative_to(APP)): found
        for path in APP.rglob("*.py")
        if path.name != "clock.py" and (found := direct_time_calls(path.read_text(encoding="utf8")))
    }
    assert problems == {}


@pytest.mark.parametrize(
    "bad", ["date.today()", "datetime.now()", "datetime.now(UTC)", "datetime.utcnow()"]
)
def test_scanner_catches_direct_calls(bad):
    assert direct_time_calls(bad)
