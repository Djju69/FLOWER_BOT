"""
Async database layer for the flower shop bot.
Uses SQLite for local development; can be swapped to asyncpg with the same interface.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import aiosqlite

from .models import Category, Product, Order, SupportMessage


class Database:
    """Lightweight async wrapper around aiosqlite."""

    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self._conn: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path.as_posix())
        await self._conn.execute("PRAGMA foreign_keys = ON;")
        await self._conn.execute("PRAGMA journal_mode = WAL;")

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def create_schema(self) -> None:
        """Create tables if they do not exist."""
        if not self._conn:
            raise RuntimeError("Database connection is not initialized")

        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                price_from BOOLEAN NOT NULL DEFAULT 0,
                description TEXT NOT NULL,
                photo_file_id TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                product_id INTEGER NOT NULL REFERENCES products(id),
                price INTEGER NOT NULL,
                delivery_date TEXT NOT NULL,
                delivery_time TEXT NOT NULL,
                address TEXT NOT NULL,
                card_text TEXT,
                phone TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '🟡 Новый',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS support_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                text TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await self._conn.commit()

        # Seed default categories if empty
        if not await self.get_categories():
            defaults = [
                "🌹 Розы",
                "🌸 Сезонные",
                "🎁 В коробке",
                "💍 Свадебные",
                "🌿 Мини",
                "🌈 Индивидуальный заказ",
            ]
            for name in defaults:
                await self.add_category(name)

    async def add_category(self, name: str) -> int:
        async with self._lock:
            cursor = await self._conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
            await self._conn.commit()
            return cursor.lastrowid

    async def rename_category(self, category_id: int, new_name: str) -> None:
        async with self._lock:
            await self._conn.execute("UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id))
            await self._conn.commit()

    async def delete_category(self, category_id: int) -> None:
        async with self._lock:
            await self._conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            await self._conn.commit()

    async def get_categories(self) -> List[Category]:
        cursor = await self._conn.execute("SELECT id, name, created_at FROM categories ORDER BY id ASC")
        rows = await cursor.fetchall()
        return [Category(id=row[0], name=row[1], created_at=datetime.fromisoformat(row[2])) for row in rows]

    async def add_product(
        self,
        category_id: int,
        name: str,
        price: int,
        price_from: bool,
        description: str,
        photo_file_id: str,
        is_active: bool = True,
    ) -> int:
        async with self._lock:
            cursor = await self._conn.execute(
                """
                INSERT INTO products (category_id, name, price, price_from, description, photo_file_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (category_id, name, price, int(price_from), description, photo_file_id, int(is_active)),
            )
            await self._conn.commit()
            return cursor.lastrowid

    async def update_product(self, product_id: int, **fields: object) -> None:
        if not fields:
            return
        columns = ", ".join(f"{key} = ?" for key in fields)
        values: List[object] = list(fields.values())
        values.append(product_id)
        async with self._lock:
            await self._conn.execute(f"UPDATE products SET {columns} WHERE id = ?", values)
            await self._conn.commit()

    async def delete_product(self, product_id: int) -> None:
        async with self._lock:
            await self._conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            await self._conn.commit()

    async def get_products_by_category(
        self, category_id: int, limit: int, offset: int = 0
    ) -> List[Product]:
        cursor = await self._conn.execute(
            """
            SELECT id, category_id, name, price, price_from, description, photo_file_id, is_active, created_at
            FROM products
            WHERE category_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (category_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [
            Product(
                id=row[0],
                category_id=row[1],
                name=row[2],
                price=row[3],
                price_from=bool(row[4]),
                description=row[5],
                photo_file_id=row[6],
                is_active=bool(row[7]),
                created_at=datetime.fromisoformat(row[8]),
            )
            for row in rows
        ]

    async def count_products_in_category(self, category_id: int) -> int:
        cursor = await self._conn.execute(
            "SELECT COUNT(*) FROM products WHERE category_id = ? AND is_active = 1", (category_id,)
        )
        row = await cursor.fetchone()
        return int(row[0]) if row else 0

    async def get_product(self, product_id: int) -> Optional[Product]:
        cursor = await self._conn.execute(
            """
            SELECT id, category_id, name, price, price_from, description, photo_file_id, is_active, created_at
            FROM products WHERE id = ?
            """,
            (product_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return Product(
            id=row[0],
            category_id=row[1],
            name=row[2],
            price=row[3],
            price_from=bool(row[4]),
            description=row[5],
            photo_file_id=row[6],
            is_active=bool(row[7]),
            created_at=datetime.fromisoformat(row[8]),
        )

    async def create_order(
        self,
        user_id: int,
        username: Optional[str],
        product_id: int,
        price: int,
        delivery_date: str,
        delivery_time: str,
        address: str,
        card_text: Optional[str],
        phone: str,
        status: str = "🟡 Новый",
    ) -> int:
        async with self._lock:
            cursor = await self._conn.execute(
                """
                INSERT INTO orders (user_id, username, product_id, price, delivery_date, delivery_time, address, card_text, phone, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, username, product_id, price, delivery_date, delivery_time, address, card_text, phone, status),
            )
            await self._conn.commit()
            return cursor.lastrowid

    async def update_order_status(self, order_id: int, status: str) -> None:
        async with self._lock:
            await self._conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
            await self._conn.commit()

    async def get_user_orders(self, user_id: int, limit: int = 10) -> List[Order]:
        cursor = await self._conn.execute(
            """
            SELECT id, user_id, username, product_id, price, delivery_date, delivery_time, address, card_text, phone, status, created_at
            FROM orders WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            Order(
                id=row[0],
                user_id=row[1],
                username=row[2],
                product_id=row[3],
                price=row[4],
                delivery_date=row[5],
                delivery_time=row[6],
                address=row[7],
                card_text=row[8],
                phone=row[9],
                status=row[10],
                created_at=datetime.fromisoformat(row[11]),
            )
            for row in rows
        ]

    async def get_last_completed_orders(self, user_id: int, limit: int = 3) -> List[Order]:
        cursor = await self._conn.execute(
            """
            SELECT id, user_id, username, product_id, price, delivery_date, delivery_time, address, card_text, phone, status, created_at
            FROM orders
            WHERE user_id = ? AND status = '🟢 Завершён'
            ORDER BY created_at DESC LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            Order(
                id=row[0],
                user_id=row[1],
                username=row[2],
                product_id=row[3],
                price=row[4],
                delivery_date=row[5],
                delivery_time=row[6],
                address=row[7],
                card_text=row[8],
                phone=row[9],
                status=row[10],
                created_at=datetime.fromisoformat(row[11]),
            )
            for row in rows
        ]

    async def get_order(self, order_id: int) -> Optional[Order]:
        cursor = await self._conn.execute(
            """
            SELECT id, user_id, username, product_id, price, delivery_date, delivery_time, address, card_text, phone, status, created_at
            FROM orders WHERE id = ?
            """,
            (order_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return Order(
            id=row[0],
            user_id=row[1],
            username=row[2],
            product_id=row[3],
            price=row[4],
            delivery_date=row[5],
            delivery_time=row[6],
            address=row[7],
            card_text=row[8],
            phone=row[9],
            status=row[10],
            created_at=datetime.fromisoformat(row[11]),
        )

    async def save_support_message(self, user_id: int, username: Optional[str], text: str) -> int:
        async with self._lock:
            cursor = await self._conn.execute(
                "INSERT INTO support_messages (user_id, username, text) VALUES (?, ?, ?)", (user_id, username, text)
            )
            await self._conn.commit()
            return cursor.lastrowid


