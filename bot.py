import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers.media import cleanup, router as media_router
from handlers.start import router as start_router


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(media_router)
    dp.shutdown.register(cleanup)

    try:
        # Keep pending updates on restart; do not silently discard user messages.
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
