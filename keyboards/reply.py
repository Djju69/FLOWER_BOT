"""Reply keyboards used in the bot."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Main menu with canonical buttons."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Магазин"), KeyboardButton(text="📦 Заказы")],
            [KeyboardButton(text="🔁 Повторить заказ"), KeyboardButton(text="💬 Поддержка")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


def phone_request_kb() -> ReplyKeyboardMarkup:
    """Reply keyboard to request phone contact."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить мой номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def location_request_kb() -> ReplyKeyboardMarkup:
    """Reply keyboard to request user location."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

