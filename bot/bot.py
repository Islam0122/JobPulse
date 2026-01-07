import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
import config
from handlers import start, profile, echo, subscription, insights, vacancies, profile_edit,comment
from middlewares.subscription_middleware import SubscriptionMiddleware

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    storage = RedisStorage.from_url(config.REDIS_URL)
    dp = Dispatcher(storage=storage)
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    dp.include_router(subscription.router)  # Проверка подписки
    dp.include_router(start.router)  # Команды /start, онбординг
    dp.include_router(profile.router)  # Профиль, настройки
    dp.include_router(profile_edit.router)
    dp.include_router(vacancies.router)  # Просмотр вакансий
    dp.include_router(insights.router)  # Аналитика
    dp.include_router(comment.router)
    dp.include_router(echo.router)  # Эхо (должен быть последним)

    logger.info("🤖 Бот запущен и готов к работе!")
    logger.info(f"📡 Backend API: {config.BACKEND_URL}")
    logger.info(f"🔴 Redis: {config.REDIS_URL}")
    logger.info("🔐 Middleware проверки подписки активирован")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    finally:
        await bot.session.close()
        await storage.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")