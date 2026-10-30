"""Common handlers: /start and /help."""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router(name="common")

HELP_TEXT = (
    "Я — бот-менеджер задач. Что умею:\n\n"
    "/projects — список твоих проектов\n"
    "/new_project — создать проект\n"
    "/new_task — создать задачу\n"
    "/today — задачи на сегодня\n"
    "/help — эта справка"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Greet the user on /start."""
    await message.answer(f"Привет, {message.from_user.first_name}! 👋\n\n" + HELP_TEXT)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Show help text."""
    await message.answer(HELP_TEXT)
