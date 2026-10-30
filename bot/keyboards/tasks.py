"""Inline keyboards for task flows."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

STATUS_EMOJI = {"todo": "⬜", "in_progress": "🔵", "done": "✅"}
STATUS_LABEL = {"todo": "К выполнению", "in_progress": "В работе", "done": "Выполнена"}
PRIORITY_EMOJI = {"low": "🟢", "medium": "🟡", "high": "🔴"}
PRIORITY_LABEL = {"low": "Низкий", "medium": "Средний", "high": "Высокий"}

PAGE_SIZE = 10


def projects_select_keyboard(projects: list[dict]) -> InlineKeyboardMarkup:
    """Project picker for the /new_task flow."""
    builder = InlineKeyboardBuilder()
    for project in projects:
        builder.button(text=f"📁 {project['name']}", callback_data=f"nt:prj:{project['id']}")
    builder.adjust(1)
    return builder.as_markup()


def priority_keyboard() -> InlineKeyboardMarkup:
    """Priority picker for the /new_task flow."""
    builder = InlineKeyboardBuilder()
    for value in ("low", "medium", "high"):
        builder.button(
            text=f"{PRIORITY_EMOJI[value]} {PRIORITY_LABEL[value]}",
            callback_data=f"nt:pri:{value}",
        )
    builder.adjust(3)
    return builder.as_markup()


def tasks_keyboard(
    tasks: list[dict], project_id: int, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    """Task buttons plus pagination controls."""
    builder = InlineKeyboardBuilder()
    for task in tasks:
        title = task["title"][:40]
        builder.button(
            text=f"{STATUS_EMOJI[task['status']]} {title}",
            callback_data=f"task:view:{task['id']}:{project_id}:{page}",
        )
    builder.adjust(1)

    nav = InlineKeyboardBuilder()
    if page > 0:
        nav.button(text="◀️", callback_data=f"task:list:{project_id}:{page - 1}")
    nav.button(text=f"{page + 1}/{total_pages}", callback_data="task:noop")
    if page < total_pages - 1:
        nav.button(text="▶️", callback_data=f"task:list:{project_id}:{page + 1}")
    builder.attach(nav)

    back = InlineKeyboardBuilder()
    back.button(text="⬅️ К проекту", callback_data=f"prj:view:{project_id}")
    builder.attach(back)
    return builder.as_markup()


def task_actions_keyboard(task_id: int, project_id: int, page: int) -> InlineKeyboardMarkup:
    """Actions available on a task card."""
    builder = InlineKeyboardBuilder()
    for value in ("todo", "in_progress", "done"):
        builder.button(
            text=f"{STATUS_EMOJI[value]} {STATUS_LABEL[value]}",
            callback_data=f"task:status:{task_id}:{value}:{project_id}:{page}",
        )
    builder.button(text="🗑 Удалить", callback_data=f"task:del:{task_id}:{project_id}:{page}")
    builder.button(text="⬅️ К задачам", callback_data=f"task:list:{project_id}:{page}")
    builder.adjust(3, 1, 1)
    return builder.as_markup()


def confirm_task_delete_keyboard(task_id: int, project_id: int, page: int) -> InlineKeyboardMarkup:
    """Yes/no confirmation before deleting a task."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Да, удалить", callback_data=f"task:delyes:{task_id}:{project_id}:{page}"
    )
    builder.button(text="❌ Отмена", callback_data=f"task:view:{task_id}:{project_id}:{page}")
    builder.adjust(2)
    return builder.as_markup()
