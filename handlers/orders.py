"""Order-related handlers and FSM."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..config import Settings
from ..database.db import Database
from ..keyboards.inline import (
    order_date_kb,
    order_time_kb,
    card_text_kb,
    orders_list_nav_kb,
)
from ..keyboards.reply import main_menu_kb, phone_request_kb, location_request_kb
from ..states.order import OrderStates
from ..utils.helpers import format_price, is_phone_valid, normalize_card_text
from ..utils.notifications import notify_admins


orders_router = Router(name="orders")


@orders_router.message(F.text == "📦 Заказы")
async def show_orders(message: Message, db: Database) -> None:
    orders = await db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("У вас пока нет заказов 😊\nНажмите «🛍 Магазин», чтобы сделать первый!")
        return
    text_lines = ["📦 ВАШИ ЗАКАЗЫ", ""]
    for idx, order in enumerate(orders, start=1):
        text_lines.append(f"{idx}️⃣ Заказ #{order.id} — {order.status}")
        product = await db.get_product(order.product_id)
        if product:
            text_lines.append(f"   🌹 {product.name}")
        text_lines.append(f"   📅 Доставка: {order.delivery_date}, {order.delivery_time}")
        text_lines.append(f"   💰 {format_price(order.price)}")
        text_lines.append("")
        await message.answer("\n".join(text_lines[-5:]), reply_markup=orders_list_nav_kb(order.id))
    await message.answer("🏠 Главное меню", reply_markup=main_menu_kb())


@orders_router.callback_query(F.data.startswith("order_details:"))
async def order_details(cb: CallbackQuery, db: Database) -> None:
    order_id = int(cb.data.split(":")[1])
    order = await db.get_order(order_id)
    if not order:
        await cb.answer("Заказ не найден", show_alert=True)
        return
    product = await db.get_product(order.product_id)
    product_name = product.name if product else "Букет"
    card_text = order.card_text or "Без открытки"
    text = (
        f"📋 ЗАКАЗ #{order.id}\n\n"
        f"{order.status}\n\n"
        f"🌹 Букет: {product_name}\n"
        f"💰 Сумма: {format_price(order.price)}\n"
        f"💳 Предоплата: {format_price(int(order.price * 0.5))}\n\n"
        f"📅 Дата доставки: {order.delivery_date}\n"
        f"⏰ Время: {order.delivery_time}\n"
        f"📍 Адрес: {order.address}\n"
        f"💌 Открытка: {card_text}\n"
        f"📞 Телефон: {order.phone}\n"
        f"🕐 Создан: {order.created_at.strftime('%Y-%m-%d %H:%M')}"
    )
    await cb.message.answer(text, reply_markup=orders_list_nav_kb(order.id))
    await cb.answer()


@orders_router.message(F.text == "🔁 Повторить заказ")
async def repeat_order(message: Message, db: Database, state: FSMContext) -> None:
    orders = await db.get_last_completed_orders(message.from_user.id, limit=3)
    if not orders:
        await message.answer("У вас пока нет завершённых заказов для повтора 😊")
        return
    await state.set_data({})
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    header = ["🔁 ПОВТОРИТЬ ЗАКАЗ", "", "Выберите заказ из истории:"]
    await message.answer("\n".join(header))
    for order in orders:
        product = await db.get_product(order.product_id)
        product_name = product.name if product else "Букет"
        text = (
            f"🔁 Заказ #{order.id}\n"
            f"🌹 {product_name}\n"
            f"📅 Доставлен: {order.delivery_date}\n"
            f"💰 {format_price(order.price)}"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=f"🔁 Повторить заказ #{order.id}", callback_data=f"repeat_order:{order.id}")]]
        )
        await message.answer(text, reply_markup=kb)
    await message.answer("🏠 Главное меню", reply_markup=main_menu_kb())


@orders_router.callback_query(F.data.startswith("repeat_order:"))
async def repeat_order_callback(cb: CallbackQuery, state: FSMContext, db: Database) -> None:
    order_id = int(cb.data.split(":")[1])
    order = await db.get_order(order_id)
    if not order:
        await cb.answer("Заказ не найден", show_alert=True)
        return
    product = await db.get_product(order.product_id)
    product_name = product.name if product else "Букет"
    await state.update_data(
        product_id=order.product_id,
        product_price=order.price,
        product_name=product_name,
    )
    await cb.message.answer(f"Повторный заказ на основе #{order.id}")
    await cb.message.answer("📅 Выберите дату доставки:", reply_markup=order_date_kb(include_today=True))
    await state.set_state(OrderStates.waiting_for_delivery_date)
    await cb.answer()


@orders_router.callback_query(OrderStates.waiting_for_delivery_date, F.data.startswith("date_selected:"))
async def date_selected(cb: CallbackQuery, state: FSMContext) -> None:
    value = cb.data.split(":", 1)[1]
    if value == "today":
        selected = date.today()
    elif value == "tomorrow":
        selected = date.today() + timedelta(days=1)
    else:
        selected = date.fromisoformat(value)
    await state.update_data(delivery_date=selected.isoformat())
    await cb.message.answer("⏰ Выберите время доставки:", reply_markup=order_time_kb())
    await state.set_state(OrderStates.waiting_for_delivery_time)
    await cb.answer()


@orders_router.callback_query(OrderStates.waiting_for_delivery_time, F.data.startswith("time_selected:"))
async def time_selected(cb: CallbackQuery, state: FSMContext) -> None:
    slot = cb.data.split(":", 1)[1]
    await state.update_data(delivery_time=slot)
    await cb.message.answer(
        "📍 Укажите адрес доставки:",
        reply_markup=location_request_kb(),
    )
    await state.set_state(OrderStates.waiting_for_address)
    await cb.answer()


@orders_router.callback_query(OrderStates.waiting_for_delivery_time, F.data == "back_to_date")
async def back_to_date(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OrderStates.waiting_for_delivery_date)
    await cb.message.answer("📅 Выберите дату доставки:", reply_markup=order_date_kb(include_today=True))
    await cb.answer()


@orders_router.callback_query(F.data == "order_cancel")
async def cancel_order(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.message.answer("❌ Заказ отменён", reply_markup=main_menu_kb())
    await cb.answer()


@orders_router.message(OrderStates.waiting_for_address, F.location)
async def address_location(message: Message, state: FSMContext) -> None:
    loc = message.location
    address_text = f"geo:{loc.latitude},{loc.longitude}"
    await state.update_data(address=address_text)
    await message.answer("Укажите квартиру/офис/этаж/домофон текстом.")


@orders_router.message(OrderStates.waiting_for_address, F.text)
async def address_text(message: Message, state: FSMContext) -> None:
    if len(message.text.strip()) < 10:
        await message.answer("Пожалуйста, укажите полный адрес (минимум 10 символов).")
        return
    await state.update_data(address=message.text.strip())
    await message.answer("💌 Хотите добавить открытку?", reply_markup=card_text_kb())
    await state.set_state(OrderStates.waiting_for_card_text)


@orders_router.callback_query(OrderStates.waiting_for_card_text, F.data == "card_write")
async def card_write(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.message.answer("Напишите текст открытки (до 200 символов).")
    await cb.answer()


@orders_router.callback_query(OrderStates.waiting_for_card_text, F.data == "card_skip")
async def card_skip(cb: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(card_text=None)
    await ask_phone(cb.message, state)
    await cb.answer()


@orders_router.callback_query(OrderStates.waiting_for_card_text, F.data == "card_back")
async def card_back(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OrderStates.waiting_for_address)
    await cb.message.answer("📍 Укажите адрес доставки:", reply_markup=location_request_kb())
    await cb.answer()


@orders_router.message(OrderStates.waiting_for_card_text, F.text)
async def card_text(message: Message, state: FSMContext) -> None:
    text = normalize_card_text(message.text)
    await state.update_data(card_text=text)
    await message.answer(f"Ваша открытка:\n\n{text}\n\nВсё верно?")
    await ask_phone(message, state)


async def ask_phone(message: Message, state: FSMContext) -> None:
    await state.set_state(OrderStates.waiting_for_phone)
    await message.answer("📞 Укажите контактный номер для связи:", reply_markup=phone_request_kb())


@orders_router.message(OrderStates.waiting_for_phone, F.contact)
async def phone_contact(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await show_summary(message, state)


@orders_router.message(OrderStates.waiting_for_phone, F.text)
async def phone_text(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if not is_phone_valid(phone):
        await message.answer("Введите номер в формате +XX XXX XXX XXXX или 0XXXXXXXXX.")
        return
    await state.update_data(phone=phone)
    await show_summary(message, state)


async def show_summary(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    product_name = data.get("product_name", "Букет")
    price = data.get("product_price", 0)
    delivery_date = data.get("delivery_date")
    delivery_time = data.get("delivery_time")
    address = data.get("address")
    card_text = data.get("card_text") or "Без открытки"
    phone = data.get("phone")
    prepayment = int(price * 0.5)

    summary = (
        "📋 ПОДТВЕРЖДЕНИЕ ЗАКАЗА\n\n"
        f"🌹 Букет: {product_name}\n"
        f"💰 Цена: {format_price(price)}\n\n"
        f"📅 Дата: {delivery_date}\n"
        f"⏰ Время: {delivery_time}\n"
        f"📍 Адрес: {address}\n"
        f"💌 Открытка: {card_text}\n"
        f"📞 Телефон: {phone}\n\n"
        f"💳 Предоплата: {format_price(prepayment)}\n\n"
        "Всё верно?"
    )
    await message.answer(
        summary,
        reply_markup=create_confirmation_kb(),
    )
    await state.set_state(OrderStates.waiting_for_confirmation)


def create_confirmation_kb():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="order_confirm")],
            [InlineKeyboardButton(text="✏️ Изменить", callback_data="order_edit")],
            [InlineKeyboardButton(text="❌ Отменить заказ", callback_data="order_cancel")],
        ]
    )


@orders_router.callback_query(OrderStates.waiting_for_confirmation, F.data == "order_edit")
async def order_edit(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OrderStates.waiting_for_delivery_date)
    await cb.message.answer("Что изменим? Начнём с даты доставки.", reply_markup=order_date_kb(include_today=True))
    await cb.answer()


@orders_router.callback_query(OrderStates.waiting_for_confirmation, F.data == "order_confirm")
async def order_confirm(cb: CallbackQuery, state: FSMContext, db: Database, settings: Settings, bot) -> None:  # type: ignore[override]
    data = await state.get_data()
    product_id = data["product_id"]
    product = await db.get_product(product_id)
    if not product:
        await cb.answer("Товар не найден", show_alert=True)
        return

    order_id = await db.create_order(
        user_id=cb.from_user.id,
        username=cb.from_user.username,
        product_id=product_id,
        price=product.price,
        delivery_date=data["delivery_date"],
        delivery_time=data["delivery_time"],
        address=data["address"],
        card_text=data.get("card_text"),
        phone=data["phone"],
    )
    prepayment = int(product.price * settings.prepayment_ratio)

    admin_text = (
        f"🔔 НОВЫЙ ЗАКАЗ #{order_id}\n\n"
        f"👤 Клиент: @{cb.from_user.username or 'unknown'} (ID: {cb.from_user.id})\n"
        f"🌹 Букет: {product.name}\n"
        f"💰 Сумма: {format_price(product.price)}\n"
        f"💳 Предоплата: {format_price(prepayment)}\n\n"
        f"📅 Дата: {data['delivery_date']}\n"
        f"⏰ Время: {data['delivery_time']}\n"
        f"📍 Адрес: {data['address']}\n"
        f"💌 Открытка: {data.get('card_text') or 'Без открытки'}\n"
        f"📞 Телефон: {data['phone']}"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять в работу", callback_data=f"admin_order_accept:{order_id}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_order_reject:{order_id}")],
        ]
    )
    await notify_admins(bot, settings.admin_ids, admin_text, reply_markup=admin_kb)

    await cb.message.answer(
        f"✅ Заказ #{order_id} оформлен!\n\n"
        f"Для подтверждения необходима предоплата:\n"
        f"💳 {format_price(prepayment)} (50%)\n\n"
        "Реквизиты для оплаты:\n"
        "📱 Номер карты: 9704 XXXX XXXX 1234\n"
        "🏦 Банк: Vietcombank\n"
        "👤 Получатель: NGUYEN VAN A\n\n"
        "После оплаты отправьте скриншот чека.\n\n"
        "📞 Вопросы? Нажмите «💬 Поддержка»",
        reply_markup=main_menu_kb(),
    )
    await state.clear()
    await cb.answer()


def _ensure_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.admin_ids


@orders_router.callback_query(F.data.startswith("admin_order_accept:"))
async def admin_order_accept(cb: CallbackQuery, db: Database, settings: Settings, bot) -> None:
    if not _ensure_admin(cb.from_user.id, settings):
        await cb.answer("Недостаточно прав", show_alert=True)
        return
    order_id = int(cb.data.split(":")[1])
    order = await db.get_order(order_id)
    if not order:
        await cb.answer("Заказ не найден", show_alert=True)
        return
    await db.update_order_status(order_id, "🔵 В работе")
    try:
        await bot.send_message(order.user_id, f"Ваш заказ #{order_id} принят в работу! 🚀")
    except Exception:
        pass
    await cb.answer("Статус обновлён")


@orders_router.callback_query(F.data.startswith("admin_order_reject:"))
async def admin_order_reject(cb: CallbackQuery, db: Database, settings: Settings, bot) -> None:
    if not _ensure_admin(cb.from_user.id, settings):
        await cb.answer("Недостаточно прав", show_alert=True)
        return
    order_id = int(cb.data.split(":")[1])
    order = await db.get_order(order_id)
    if not order:
        await cb.answer("Заказ не найден", show_alert=True)
        return
    await db.update_order_status(order_id, "❌ Отменён")
    try:
        await bot.send_message(order.user_id, f"К сожалению, заказ #{order_id} отклонён. Свяжитесь с поддержкой для уточнения.")
    except Exception:
        pass
    await cb.answer("Статус обновлён")


