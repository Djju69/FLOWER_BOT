"""Helper functions for validation and formatting."""

from __future__ import annotations

import re
from datetime import datetime, time
from typing import Optional


def format_price(price: int, price_from: bool = False) -> str:
    amount = f"{price:,}".replace(",", " ")
    return f"от {amount} VND" if price_from else f"{amount} VND"


def is_phone_valid(phone: str) -> bool:
    phone = phone.strip()
    patterns = [
        r"^\+\d{2}\s?\d{3}\s?\d{3}\s?\d{4}$",
        r"^0\d{9}$",
        r"^\+\d{9,15}$",
    ]
    return any(re.match(pattern, phone) for pattern in patterns)


def normalize_card_text(text: str) -> str:
    return text.strip()[:200]


def is_after_six_pm(now: Optional[datetime] = None) -> bool:
    now = now or datetime.now()
    return now.time() >= time(hour=18, minute=0)


