"""Shared handler helpers."""

import html

from aiogram.types import CallbackQuery, Message

from bot.services.api_client import ApiError

_ERROR_TEXTS = {
    401: "🔒 Ошибка авторизации. Отправь /start и попробуй снова.",
    404: "🔍 Не найдено — возможно, уже удалено.",
    422: "⚠️ API отклонило данные. Проверь ввод и попробуй ещё раз.",
}


async def answer_api_error(target: Message, exc: ApiError) -> None:
    """Reply with a human-readable message for an API failure."""
    text = _ERROR_TEXTS.get(exc.status_code, f"⚠️ Ошибка API ({exc.status_code}). Попробуй позже.")
    await target.answer(text)


def esc(text: object) -> str:
    """HTML-escape user-controlled text for parse_mode=HTML."""
    return html.escape(str(text))
