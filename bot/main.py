"""Bot entrypoint: aiogram polling."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import get_settings
from bot.handlers import common, projects
from bot.middlewares.auth import AuthMiddleware
from bot.services.api_client import ApiClient

logger = logging.getLogger(__name__)


def setup_logging(level: str) -> None:
    """Configure root logger with a single stdout stream handler."""
    logging.basicConfig(
        level=level.upper(),
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def main() -> None:
    """Build the dispatcher and start long polling."""
    settings = get_settings()
    setup_logging(settings.log_level)

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    api_client = ApiClient(settings.api_base_url, settings.service_key)

    dp = Dispatcher()
    dp.include_router(common.router)
    dp.include_router(projects.router)

    auth_middleware = AuthMiddleware(api_client)
    dp.message.middleware(auth_middleware)
    dp.callback_query.middleware(auth_middleware)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("bot started")
    try:
        await dp.start_polling(bot)
    finally:
        await api_client.close()


if __name__ == "__main__":
    asyncio.run(main())
