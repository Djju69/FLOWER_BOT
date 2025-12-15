"""Entry point for the flower shop Telegram bot."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .config import Settings
from .database.db import Database
from .handlers import register_handlers


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = Settings()
    settings.validate()
    db = Database(settings.db_path)
    await db.connect()
    await db.create_schema()

    bot = Bot(settings.bot_token, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())
    dp["db"] = db
    dp["settings"] = settings
    register_handlers(dp)

    try:
        await dp.start_polling(bot)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())

