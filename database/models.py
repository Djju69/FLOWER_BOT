"""
Data models for the flower shop bot.
These are lightweight containers for DB rows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Category:
    id: int
    name: str
    created_at: datetime


@dataclass
class Product:
    id: int
    category_id: int
    name: str
    price: int
    price_from: bool
    description: str
    photo_file_id: str
    is_active: bool
    created_at: datetime


@dataclass
class Order:
    id: int
    user_id: int
    username: Optional[str]
    product_id: int
    price: int
    delivery_date: str
    delivery_time: str
    address: str
    card_text: Optional[str]
    phone: str
    status: str
    created_at: datetime


@dataclass
class SupportMessage:
    id: int
    user_id: int
    username: Optional[str]
    text: str
    created_at: datetime

