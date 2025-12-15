"""User level handlers: /start, support, main menu."""

from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ..config import Settings
from ..database.db import Database
from ..keyboards.inline import support_menu_kb, support_faq_kb
from ..keyboards.reply import main_menu_kb
from ..utils.notifications import notify_admins


class SupportState(StatesGroup):
    waiting_for_message = State()


user_router = Router(name="user")


@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🌸 Добро пожаловать в Цветы Нячанг!\n\n"
        "Свежие букеты с доставкой за 1-2 часа 🚚\n"
        "Нажмите «🛍 Магазин», чтобы выбрать букет, или воспользуйтесь меню ниже.",
        reply_markup=main_menu_kb(),
    )


@user_router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await message.answer("Главное меню:", reply_markup=main_menu_kb())


@user_router.message(F.text == "💬 Поддержка")
async def support_entry(message: Message) -> None:
    await message.answer(
        "💬 ПОДДЕРЖКА\n\n"
        "👋 Привет! Чем могу помочь?\n\n"
        "🕐 Время работы: 09:00 - 21:00 (ежедневно)\n"
        "📞 Телефон: +84 XXX XXX XXX\n"
        "📧 Email: flowers@nhatrang.vn\n\n"
        "❓ Частые вопросы:",
        reply_markup=support_menu_kb(),
    )


@user_router.callback_query(F.data == "delivery_info")
async def delivery_info(cb: CallbackQuery) -> None:
    await cb.message.edit_text(
        "🚚 УСЛОВИЯ ДОСТАВКИ\n\n"
        "- Бесплатная доставка при заказе от 2,000,000 VND\n"
        "- Платная доставка: 200,000 VND\n"
        "- Доставка в течение 2-4 часов\n"
        "- Экспресс-доставка: +300,000 VND (за 1 час)",
        reply_markup=support_faq_kb(),
    )
    await cb.answer()


@user_router.callback_query(F.data == "payment_info")
async def payment_info(cb: CallbackQuery) -> None:
    await cb.message.edit_text(
        "💳 СПОСОБЫ ОПЛАТЫ\n\n"
        "- Банковский перевод (предоплата 50%)\n"
        "- Наличными курьеру (оставшиеся 50%)\n"
        "- Карты Visa/Mastercard (в разработке)",
        reply_markup=support_faq_kb(),
    )
    await cb.answer()


@user_router.callback_query(F.data == "working_hours")
async def working_hours(cb: CallbackQuery) -> None:
    await cb.message.edit_text(
        "⏰ ВРЕМЯ РАБОТЫ\n\n"
        "- Пн-Вс: 09:00 - 21:00\n"
        "- Заказы принимаются круглосуточно\n"
        "- Доставка: 09:00 - 21:00",
        reply_markup=support_faq_kb(),
    )
    await cb.answer()


@user_router.callback_query(F.data == "contact_florist")
async def contact_florist(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SupportState.waiting_for_message)
    await cb.message.answer("✍️ Напишите ваш вопрос, и мы ответим в ближайшее время.")
    await cb.answer()


@user_router.message(SupportState.waiting_for_message)
async def receive_support_message(message: Message, state: FSMContext, settings: Settings, db: Database, bot) -> None:  # type: ignore[override]
    text = message.text or ""
    support_id = await db.save_support_message(message.from_user.id, message.from_user.username, text)
    admin_text = (
        "💬 НОВОЕ СООБЩЕНИЕ\n\n"
        f"👤 От: @{message.from_user.username or 'unknown'} (ID: {message.from_user.id})\n"
        f"📝 Текст: {text}"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Ответить", url=f"tg://user?id={message.from_user.id}")],
            [InlineKeyboardButton(text="📋 Открыть профиль", url=f"https://t.me/{message.from_user.username}")],
        ]
    )
    await notify_admins(bot, settings.admin_ids, admin_text, reply_markup=kb)
    await message.answer("Спасибо! Сообщение отправлено флористу. Мы ответим в ближайшее время.")
    await state.clear()


@user_router.callback_query(F.data == "main_menu")
async def back_to_main_menu(cb: CallbackQuery) -> None:
    await cb.message.answer("Главное меню", reply_markup=main_menu_kb())
    await cb.answer()

