"""FSM states for order creation."""

from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    waiting_for_delivery_date = State()
    waiting_for_delivery_time = State()
    waiting_for_address = State()
    waiting_for_card_text = State()
    waiting_for_phone = State()
    waiting_for_confirmation = State()

