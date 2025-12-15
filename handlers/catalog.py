"""Catalog handlers: categories, product list, product details."""

from __future__ import annotations

import math
from typing import List

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputMediaPhoto

from ..database.db import Database
from ..keyboards.inline import categories_kb, products_navigation_kb, product_list_action_kb, product_detail_kb, back_to_categories_kb
from ..keyboards.reply import main_menu_kb
from ..utils.helpers import format_price


catalog_router = Router(name="catalog")

PAGE_SIZE = 5


@catalog_router.message(F.text == "🛍 Магазин")
async def show_categories(message: Message, db: Database) -> None:
    categories = await db.get_categories()
    await message.answer("Выберите категорию:", reply_markup=categories_kb(categories))


@catalog_router.callback_query(F.data == "back_to_categories")
async def cb_back_to_categories(cb: CallbackQuery, db: Database) -> None:
    categories = await db.get_categories()
    await cb.message.answer("Категории:", reply_markup=categories_kb(categories))
    await cb.answer()


@catalog_router.callback_query(F.data.startswith("category:"))
async def open_category(cb: CallbackQuery, db: Database) -> None:
    _, category_id_str = cb.data.split(":")
    category_id = int(category_id_str)
    await send_products_page(cb, db, category_id, page=1)
    await cb.answer()


@catalog_router.callback_query(F.data.startswith("next_page:") | F.data.startswith("prev_page:"))
async def paginate_products(cb: CallbackQuery, db: Database) -> None:
    parts = cb.data.split(":")
    _, category_id_str, page_str = parts
    category_id, page = int(category_id_str), int(page_str)
    await send_products_page(cb, db, category_id, page)
    await cb.answer()


async def send_products_page(cb: CallbackQuery, db: Database, category_id: int, page: int) -> None:
    total_products = await db.count_products_in_category(category_id)
    total_pages = max(1, math.ceil(total_products / PAGE_SIZE))
    page = min(max(1, page), total_pages)
    offset = (page - 1) * PAGE_SIZE
    products = await db.get_products_by_category(category_id, limit=PAGE_SIZE, offset=offset)

    categories = await db.get_categories()
    category_name = next((c.name for c in categories if c.id == category_id), "Категория")
    header = f"Товары в категории {category_name} (страница {page} из {total_pages})"
    await cb.message.answer(header)

    for product in products:
        caption = (
            f"{product.name}\n"
            f"Цена: {format_price(product.price, product.price_from)}\n\n"
            f"{product.description}"
        )
        await cb.message.answer_photo(
            product.photo_file_id,
            caption=caption,
            reply_markup=product_list_action_kb(product.id, category_id, page),
        )

    has_prev = page > 1
    has_next = page < total_pages
    await cb.message.answer(
        "Навигация по товарам:",
        reply_markup=products_navigation_kb(category_id, page, has_prev, has_next),
    )


@catalog_router.callback_query(F.data.startswith("back_to_products:"))
async def back_to_products(cb: CallbackQuery, db: Database) -> None:
    _, category_id_str, page_str = cb.data.split(":")
    await send_products_page(cb, db, int(category_id_str), int(page_str))
    await cb.answer()


@catalog_router.callback_query(F.data.startswith("product_view:"))
async def product_view(cb: CallbackQuery, db: Database) -> None:
    _, product_id_str, category_id_str, page_str = cb.data.split(":")
    product = await db.get_product(int(product_id_str))
    if not product:
        await cb.answer("Товар не найден", show_alert=True)
        return
    caption = (
        f"{product.name}\n"
        f"Цена: {format_price(product.price, product.price_from)}\n\n"
        f"{product.description}"
    )
    await cb.message.answer_photo(
        product.photo_file_id,
        caption=caption,
        reply_markup=product_detail_kb(product.id, int(category_id_str), int(page_str)),
    )
    await cb.answer()


@catalog_router.callback_query(F.data.startswith("order_start:"))
async def order_start(cb: CallbackQuery, db: Database, state, bot) -> None:  # type: ignore[override]
    from ..states.order import OrderStates
    from ..keyboards.inline import order_date_kb
    from ..utils.helpers import is_after_six_pm

    _, product_id_str, category_id_str, page_str = cb.data.split(":")
    product_id = int(product_id_str)
    product = await db.get_product(product_id)
    if not product:
        await cb.answer("Товар не найден", show_alert=True)
        return

    await state.update_data(
        product_id=product_id,
        product_price=product.price,
        product_name=product.name,
        category_id=int(category_id_str),
        category_page=int(page_str),
    )
    include_today = not is_after_six_pm()
    await cb.message.answer("📅 Выберите дату доставки:", reply_markup=order_date_kb(include_today))
    await state.set_state(OrderStates.waiting_for_delivery_date)
    await cb.answer()


@catalog_router.callback_query(F.data == "main_menu")
async def to_main_menu(cb: CallbackQuery) -> None:
    await cb.message.answer("Главное меню", reply_markup=main_menu_kb())
    await cb.answer()

