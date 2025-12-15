"""
Configuration loader for the flower shop bot.
Uses environment variables with python-dotenv support.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    """Bot configuration loaded from environment variables."""

    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    admin_ids: List[int] = field(
        default_factory=lambda: [
            int(admin.strip()) for admin in os.getenv("ADMIN_IDS", "").split(",") if admin.strip()
        ]
    )
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "flower_bot/data/bot.db"))
    admin_chat_id: int | None = field(
        default=None if not os.getenv("ADMIN_CHAT_ID") else int(os.getenv("ADMIN_CHAT_ID"))
    )
    prepayment_ratio: float = 0.5
    timezone: str = os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh")

    def validate(self) -> None:
        if not self.bot_token:
            raise RuntimeError("BOT_TOKEN is required in environment variables")


