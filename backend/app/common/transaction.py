"""Ranh giới transaction. Service không bao giờ tự commit; blueprint và lệnh CLI dùng helper này.

Dùng được theo 2 cách, và mỗi request hoặc lệnh chỉ dùng đúng 1 lần:
    with transaction():
        ...

    @transaction()
    def view(): ...
"""

from contextlib import contextmanager

from app.extensions import db


@contextmanager
def transaction():
    """Commit khi khối lệnh kết thúc bình thường. Có lỗi thì rollback và ném lại lỗi đó."""
    try:
        yield
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
