"""Notification helpers for admins."""

from __future__ import annotations

from aiogram import Bot


async def notify_admins(bot: Bot, admin_ids: list[int], text: str, **kwargs) -> None:
    """Send notification text to all admins."""
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, text, **kwargs)
        except Exception:
            continue

