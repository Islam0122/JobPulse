import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
import config

from handlers import start, profile, echo

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=config.BOT_TOKEN)

    storage = RedisStorage.from_url(
        f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}"
    )

    dp = Dispatcher(storage=storage)

    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(echo.router)

    logger.info("🤖 Бот запущен и готов к работе!")
    logger.info(f"📡 Backend API: {config.BACKEND_URL}")
    logger.info(f"🔴 Redis: {config.REDIS_HOST}:{config.REDIS_PORT}")

    try:
        await bot.delete_webhook(drop_pending_updates=True)

        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await storage.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")