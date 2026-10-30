"""Inline keyboards for project flows."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards import truncate


def projects_keyboard(projects: list[dict]) -> InlineKeyboardMarkup:
    """One button per project, opening its card."""
    builder = InlineKeyboardBuilder()
    for project in projects:
        builder.button(
            text=f"📁 {truncate(project['name'])}",
            callback_data=f"prj:view:{project['id']}",
        )
    builder.adjust(1)
    return builder.as_markup()


def project_actions_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Actions available on a project card."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Задачи", callback_data=f"task:list:{project_id}:0")
    builder.button(text="🗑 Удалить", callback_data=f"prj:del:{project_id}")
    builder.button(text="⬅️ К списку", callback_data="prj:back")
    builder.adjust(2, 1)
    return builder.as_markup()


def confirm_delete_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Yes/no confirmation before deleting a project."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"prj:delyes:{project_id}")
    builder.button(text="❌ Отмена", callback_data=f"prj:view:{project_id}")
    builder.adjust(2)
    return builder.as_markup()
