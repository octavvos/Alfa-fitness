import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import BOT_TOKEN
from .handlers import admin, client, common

logging.basicConfig(level=logging.INFO)


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN sozlanmagan. .env faylini tekshiring.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(client.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
