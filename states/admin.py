"""FSM states for admin flows."""

from aiogram.fsm.state import State, StatesGroup


class AdminAddProductStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_name = State()
    waiting_for_category = State()
    waiting_for_price = State()
    waiting_for_description = State()
    waiting_for_confirmation = State()


class AdminEditProductStates(StatesGroup):
    waiting_for_field = State()
    waiting_for_photo = State()
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_description = State()
    waiting_for_category = State()
    waiting_for_status = State()


class AdminCategoryStates(StatesGroup):
    waiting_for_action = State()
    waiting_for_name = State()
    waiting_for_new_name = State()

