"""Routers registration."""

from aiogram import Dispatcher

from .user import user_router
from .catalog import catalog_router
from .orders import orders_router
from .admin import admin_router


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(user_router)
    dp.include_router(catalog_router)
    dp.include_router(orders_router)
    dp.include_router(admin_router)

