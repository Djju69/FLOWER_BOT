"""Admin panel handlers."""

from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..config import Settings
from ..database.db import Database
from ..keyboards.inline import (
    admin_main_menu_kb,
    admin_categories_kb,
)
from ..states.admin import AdminAddProductStates, AdminCategoryStates
from ..utils.helpers import format_price


admin_router = Router(name="admin")


def is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.admin_ids


@admin_router.message(Command("admin"))
async def admin_entry(message: Message, settings: Settings) -> None:
    if not is_admin(message.from_user.id, settings):
        return
    await message.answer("🔧 АДМИН-ПАНЕЛЬ", reply_markup=admin_main_menu_kb())


@admin_router.callback_query(F.data == "admin:back")
async def admin_back(cb: CallbackQuery) -> None:
    await cb.message.edit_text("🔧 АДМИН-ПАНЕЛЬ", reply_markup=admin_main_menu_kb())
    await cb.answer()


@admin_router.callback_query(F.data == "admin:add_product")
async def admin_add_product_start(cb: CallbackQuery, state: FSMContext, settings: Settings) -> None:
    if not is_admin(cb.from_user.id, settings):
        await cb.answer("Недостаточно прав", show_alert=True)
        return
    await state.set_state(AdminAddProductStates.waiting_for_photo)
    await cb.message.answer("📸 Отправьте фото букета (JPEG/PNG, до 5MB)")
    await cb.answer()


@admin_router.message(AdminAddProductStates.waiting_for_photo, F.photo)
async def admin_add_photo(message: Message, state: FSMContext) -> None:
    file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=file_id)
    await state.set_state(AdminAddProductStates.waiting_for_name)
    await message.answer("📝 Введите название букета (3-50 символов)")


@admin_router.message(AdminAddProductStates.waiting_for_name, F.text)
async def admin_add_name(message: Message, state: FSMContext, db: Database) -> None:
    name = message.text.strip()
    if not (3 <= len(name) <= 50):
        await message.answer("Название должно быть от 3 до 50 символов.")
        return
    await state.update_data(name=name)
    categories = await db.get_categories()
    await state.set_state(AdminAddProductStates.waiting_for_category)
    await message.answer("📂 Выберите категорию:", reply_markup=admin_categories_kb(categories))


@admin_router.callback_query(AdminAddProductStates.waiting_for_category, F.data.startswith("admin:category:"))
async def admin_add_category_selected(cb: CallbackQuery, state: FSMContext) -> None:
    category_id = int(cb.data.split(":")[2])
    await state.update_data(category_id=category_id)
    await state.set_state(AdminAddProductStates.waiting_for_price)
    await cb.message.answer("💰 Введите цену (только число в VND или 'от XXXX')")
    await cb.answer()


@admin_router.message(AdminAddProductStates.waiting_for_price, F.text)
async def admin_add_price(message: Message, state: FSMContext) -> None:
    raw = message.text.strip()
    price_from = False
    if raw.lower().startswith("от"):
        price_from = True
        raw = raw[2:].strip()
    if not raw.isdigit():
        await message.answer("Введите число или 'от 1800000'.")
        return
    price = int(raw)
    await state.update_data(price=price, price_from=price_from)
    await state.set_state(AdminAddProductStates.waiting_for_description)
    await message.answer("📋 Введите описание букета (до 500 символов)")


@admin_router.message(AdminAddProductStates.waiting_for_description, F.text)
async def admin_add_description(message: Message, state: FSMContext) -> None:
    description = message.text.strip()
    if len(description) > 500:
        await message.answer("Описание должно быть до 500 символов.")
        return
    await state.update_data(description=description)
    await state.set_state(AdminAddProductStates.waiting_for_confirmation)
    data = await state.get_data()
    summary = (
        f"🌹 {data['name']}\n"
        f"💰 {format_price(data['price'], data['price_from'])}\n\n"
        f"📋 Описание:\n{description}\n\n"
        "Всё верно?"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data="admin:product_save")],
            [InlineKeyboardButton(text="✏️ Изменить", callback_data="admin:back")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="admin:cancel_add")],
        ]
    )
    await message.answer_photo(data["photo_file_id"], caption=summary, reply_markup=kb)


@admin_router.callback_query(AdminAddProductStates.waiting_for_confirmation, F.data == "admin:product_save")
async def admin_save_product(cb: CallbackQuery, state: FSMContext, db: Database, settings: Settings) -> None:
    data = await state.get_data()
    product_id = await db.add_product(
        category_id=data["category_id"],
        name=data["name"],
        price=data["price"],
        price_from=data["price_from"],
        description=data["description"],
        photo_file_id=data["photo_file_id"],
    )
    await cb.message.answer(f"✅ Товар '{data['name']}' успешно добавлен! (ID: {product_id})")
    await state.clear()
    await cb.answer()


@admin_router.callback_query(AdminAddProductStates.waiting_for_confirmation, F.data == "admin:cancel_add")
async def admin_cancel_add(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.message.answer("Операция добавления товара отменена.")
    await cb.answer()


@admin_router.callback_query(F.data == "admin:categories")
async def admin_categories(cb: CallbackQuery, db: Database, settings: Settings, state: FSMContext) -> None:
    if not is_admin(cb.from_user.id, settings):
        await cb.answer("Недостаточно прав", show_alert=True)
        return
    await state.set_state(AdminCategoryStates.waiting_for_action)
    cats = await db.get_categories()
    kb = admin_categories_kb(cats)
    await cb.message.edit_text("📂 Управление категориями", reply_markup=kb)
    await cb.answer()


@admin_router.callback_query(AdminCategoryStates.waiting_for_action, F.data == "admin:add_category")
async def admin_add_category(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminCategoryStates.waiting_for_name)
    await cb.message.answer("Введите название новой категории (с эмодзи).")
    await cb.answer()


@admin_router.message(AdminCategoryStates.waiting_for_name, F.text)
async def admin_category_name(message: Message, state: FSMContext, db: Database) -> None:
    name = message.text.strip()
    await db.add_category(name)
    await message.answer(f"Категория '{name}' добавлена.")
    await state.clear()


