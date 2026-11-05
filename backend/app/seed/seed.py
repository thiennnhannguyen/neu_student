"""Lệnh seed. Giai đoạn 01 để trống; dữ liệu mẫu được thêm ở giai đoạn 03."""

import click
from flask import Flask


def run_seed() -> int:
    """Nạp dữ liệu mẫu và trả về số bản ghi đã tạo."""
    return 0


def register_seed_command(app: Flask) -> None:
    @app.cli.command("seed")
    def seed_command():
        """Nạp dữ liệu mẫu."""
        created = run_seed()
        click.echo(f"Seed xong: {created} bản ghi (chưa có dữ liệu mẫu).")
