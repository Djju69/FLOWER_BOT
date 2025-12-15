"""Inline keyboards used across the bot."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..database.models import Category, Order, Product


def categories_kb(categories: Iterable[Category]) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=category.name, callback_data=f"category:{category.id}")] for category in categories]
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_navigation_kb(category_id: int, page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    buttons: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []
    if has_prev:
        row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"prev_page:{category_id}:{page-1}"))
    if has_next:
        row.append(InlineKeyboardButton(text="➡️ Далее", callback_data=f"next_page:{category_id}:{page+1}"))
    if row:
        buttons.append(row)
    buttons.append(
        [
            InlineKeyboardButton(text="📂 К категориям", callback_data="back_to_categories"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_list_action_kb(product_id: int, category_id: int, page: int) -> InlineKeyboardMarkup:
    """Actions shown on product cards inside the paginated list."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Заказать", callback_data=f"product_view:{product_id}:{category_id}:{page}")],
        ]
    )


def product_detail_kb(product_id: int, category_id: int, page: int) -> InlineKeyboardMarkup:
    """Actions on the detailed product card."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Заказать", callback_data=f"order_start:{product_id}:{category_id}:{page}")],
            [InlineKeyboardButton(text="⬅️ Назад к товарам", callback_data=f"back_to_products:{category_id}:{page}")],
        ]
    )


def back_to_categories_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📂 К категориям", callback_data="back_to_categories")]])


def order_date_kb(include_today: bool) -> InlineKeyboardMarkup:
    """Builds keyboard for selecting delivery date."""
    buttons: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []
    if include_today:
        row.append(InlineKeyboardButton(text="🚀 Сегодня", callback_data="date_selected:today"))
    row.append(InlineKeyboardButton(text="📆 Завтра", callback_data="date_selected:tomorrow"))
    buttons.append(row)

    # Next 14 days calendar style grid
    today = date.today()
    days = []
    for i in range(14):
        target = today + timedelta(days=i)
        days.append(InlineKeyboardButton(text=target.strftime("%d.%m"), callback_data=f"date_selected:{target.isoformat()}"))
    # Arrange 7 days per row
    buttons.extend([days[i : i + 7] for i in range(0, len(days), 7)])

    buttons.append([InlineKeyboardButton(text="❌ Отменить заказ", callback_data="order_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def order_time_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="09:00 - 12:00", callback_data="time_selected:09:00-12:00")],
            [InlineKeyboardButton(text="12:00 - 15:00", callback_data="time_selected:12:00-15:00")],
            [InlineKeyboardButton(text="15:00 - 18:00", callback_data="time_selected:15:00-18:00")],
            [InlineKeyboardButton(text="18:00 - 21:00", callback_data="time_selected:18:00-21:00")],
            [InlineKeyboardButton(text="⬅️ Назад к дате", callback_data="back_to_date")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="order_cancel")],
        ]
    )


def card_text_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Написать текст", callback_data="card_write")],
            [InlineKeyboardButton(text="❌ Без открытки", callback_data="card_skip")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="card_back")],
        ]
    )


def support_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать флористу", callback_data="contact_florist")],
            [InlineKeyboardButton(text="🚚 Условия доставки", callback_data="delivery_info")],
            [InlineKeyboardButton(text="💳 Способы оплаты", callback_data="payment_info")],
            [InlineKeyboardButton(text="⏰ Время работы", callback_data="working_hours")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
        ]
    )


def support_faq_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]]
    )


def admin_main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin:add_product")],
            [InlineKeyboardButton(text="✏️ Редактировать товар", callback_data="admin:edit_product")],
            [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin:delete_product")],
            [InlineKeyboardButton(text="📂 Управление категориями", callback_data="admin:categories")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
            [InlineKeyboardButton(text="📦 Все заказы", callback_data="admin:orders")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
        ]
    )


def admin_categories_kb(categories: Iterable[Category]) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=cat.name, callback_data=f"admin:category:{cat.id}")] for cat in categories]
    buttons.append(
        [
            InlineKeyboardButton(text="➕ Добавить категорию", callback_data="admin:add_category"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_edit_product_kb(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Изменить фото", callback_data=f"admin:edit_photo:{product_id}")],
            [InlineKeyboardButton(text="📝 Изменить название", callback_data=f"admin:edit_name:{product_id}")],
            [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"admin:edit_price:{product_id}")],
            [InlineKeyboardButton(text="📋 Изменить описание", callback_data=f"admin:edit_description:{product_id}")],
            [InlineKeyboardButton(text="📂 Изменить категорию", callback_data=f"admin:edit_category:{product_id}")],
            [InlineKeyboardButton(text="🔄 Изменить статус", callback_data=f"admin:toggle_status:{product_id}")],
            [InlineKeyboardButton(text="🗑 Удалить товар", callback_data=f"admin:delete:{product_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back_products")],
        ]
    )


def orders_list_nav_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Детали", callback_data=f"order_details:{order_id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
        ]
    )

