"""Task handlers: /new_task, /today, inline task list with pagination."""

import logging
from datetime import date, datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.utils import answer_api_error, esc
from bot.keyboards.tasks import (
    PAGE_SIZE,
    PRIORITY_EMOJI,
    PRIORITY_LABEL,
    STATUS_EMOJI,
    STATUS_LABEL,
    confirm_task_delete_keyboard,
    priority_keyboard,
    projects_select_keyboard,
    task_actions_keyboard,
    tasks_keyboard,
)
from bot.services.api_client import ApiError, UserApi
from bot.states.forms import NewTaskForm

logger = logging.getLogger(__name__)

router = Router(name="tasks")


def _task_card(task: dict) -> str:
    """Render a task as an HTML card."""
    description = task.get("description") or "—"
    due = task["due_date"] or "—"
    status = STATUS_EMOJI[task["status"]] + " " + STATUS_LABEL[task["status"]]
    priority = PRIORITY_EMOJI[task["priority"]] + " " + PRIORITY_LABEL[task["priority"]]
    return (
        f"{STATUS_EMOJI[task['status']]} <b>{esc(task['title'])}</b>\n\n"
        f"{esc(description)}\n\n"
        f"Статус: {status}\n"
        f"Приоритет: {priority}\n"
        f"Дедлайн: {due}"
    )


# ------------------------------------------------------------------ /new_task
@router.message(Command("new_task"))
async def cmd_new_task(message: Message, state: FSMContext, api: UserApi) -> None:
    """Start the task-creation FSM: pick a project first."""
    try:
        projects = await api.list_projects()
    except ApiError as exc:
        await answer_api_error(message, exc)
        return

    if not projects:
        await message.answer("Сначала создай проект: /new_project")
        return

    if len(projects) == 1:
        await state.update_data(project_id=projects[0]["id"])
        await state.set_state(NewTaskForm.title)
        await message.answer("📝 Название задачи? (до 300 символов)")
        return

    await state.set_state(NewTaskForm.project)
    await message.answer(
        "В какой проект добавить задачу?",
        reply_markup=projects_select_keyboard(projects),
    )


@router.callback_query(NewTaskForm.project, F.data.startswith("nt:prj:"))
async def nt_project(callback: CallbackQuery, state: FSMContext) -> None:
    """Collect the chosen project."""
    project_id = int(callback.data.rsplit(":", 1)[1])
    await state.update_data(project_id=project_id)
    await state.set_state(NewTaskForm.title)
    await callback.message.edit_text("📝 Название задачи? (до 300 символов)")
    await callback.answer()


@router.message(NewTaskForm.title)
async def nt_title(message: Message, state: FSMContext) -> None:
    """Collect the task title."""
    title = (message.text or "").strip()
    if not 1 <= len(title) <= 300:
        await message.answer("Название должно быть от 1 до 300 символов. Ещё раз:")
        return
    await state.update_data(title=title)
    await state.set_state(NewTaskForm.description)
    await message.answer("Описание задачи? Или /skip, чтобы пропустить.")


@router.message(NewTaskForm.description, Command("skip"))
async def nt_description_skip(message: Message, state: FSMContext) -> None:
    """Skip the description step."""
    await state.update_data(description=None)
    await _ask_priority(message, state)


@router.message(NewTaskForm.description)
async def nt_description(message: Message, state: FSMContext) -> None:
    """Collect the description."""
    await state.update_data(description=(message.text or "").strip() or None)
    await _ask_priority(message, state)


async def _ask_priority(message: Message, state: FSMContext) -> None:
    await state.set_state(NewTaskForm.priority)
    await message.answer("Приоритет?", reply_markup=priority_keyboard())


@router.callback_query(NewTaskForm.priority, F.data.startswith("nt:pri:"))
async def nt_priority(callback: CallbackQuery, state: FSMContext) -> None:
    """Collect the chosen priority."""
    priority = callback.data.rsplit(":", 1)[1]
    await state.update_data(priority=priority)
    await state.set_state(NewTaskForm.due_date)
    await callback.message.edit_text("🗓 Дедлайн? Формат ДД.ММ.ГГГГ, или /skip.")
    await callback.answer()


@router.message(NewTaskForm.due_date, Command("skip"))
async def nt_due_skip(message: Message, state: FSMContext, api: UserApi) -> None:
    """Create the task without a due date."""
    await _create_task(message, state, api, due_date=None)


@router.message(NewTaskForm.due_date)
async def nt_due_date(message: Message, state: FSMContext, api: UserApi) -> None:
    """Parse the due date and create the task."""
    raw = (message.text or "").strip()
    try:
        parsed = datetime.strptime(raw, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Не понял дату. Формат ДД.ММ.ГГГГ, или /skip.")
        return
    await _create_task(message, state, api, due_date=parsed)


async def _create_task(
    message: Message, state: FSMContext, api: UserApi, due_date: date | None
) -> None:
    data = await state.get_data()
    await state.clear()
    try:
        task = await api.create_task(
            project_id=data["project_id"],
            title=data["title"],
            description=data.get("description"),
            priority=data["priority"],
            due_date=due_date.isoformat() if due_date else None,
        )
    except ApiError as exc:
        await answer_api_error(message, exc)
        return
    await message.answer(
        f"✅ Задача <b>{esc(task['title'])}</b> создана "
        f"({PRIORITY_EMOJI[task['priority']]} {PRIORITY_LABEL[task['priority']]})."
    )


# --------------------------------------------------------------------- /today
@router.message(Command("today"))
async def cmd_today(message: Message, api: UserApi) -> None:
    """Show unfinished tasks due today across all projects.

    # SIMPLIFIED: due-today filtering is done bot-side; the API has no
    # aggregate endpoint yet.
    """
    try:
        projects = await api.list_projects()
    except ApiError as exc:
        await answer_api_error(message, exc)
        return

    today = date.today().isoformat()
    lines: list[str] = []
    for project in projects:
        try:
            tasks = await api.list_tasks(project["id"])
        except ApiError as exc:
            await answer_api_error(message, exc)
            return
        todays = [t for t in tasks if t["due_date"] == today and t["status"] != "done"]
        if todays:
            lines.append(f"📁 <b>{esc(project['name'])}</b>")
            for task in todays:
                lines.append(
                    f"  {STATUS_EMOJI[task['status']]} {esc(task['title'])} "
                    f"{PRIORITY_EMOJI[task['priority']]}"
                )

    if not lines:
        await message.answer("На сегодня задач нет 🎉")
    else:
        await message.answer("🗓 Задачи на сегодня:\n\n" + "\n".join(lines))


# ------------------------------------------------------------- inline: list
@router.callback_query(F.data == "task:noop")
async def cb_noop(callback: CallbackQuery) -> None:
    """Ignore taps on the page indicator."""
    await callback.answer()


async def _render_task_list(message: Message, api: UserApi, project_id: int, page: int) -> bool:
    """Render a paginated task list. False if the project could not be read."""
    try:
        tasks = await api.list_tasks(project_id)
    except ApiError:
        return False

    if not tasks:
        await message.edit_text("Задач пока нет. Добавь первую: /new_task")
        return True

    total_pages = (len(tasks) + PAGE_SIZE - 1) // PAGE_SIZE
    page = min(page, total_pages - 1)
    chunk = tasks[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
    await message.edit_text(
        "📋 Задачи проекта:",
        reply_markup=tasks_keyboard(chunk, project_id, page, total_pages),
    )
    return True


@router.callback_query(F.data.startswith("task:list:"))
async def cb_task_list(callback: CallbackQuery, api: UserApi) -> None:
    """Render a paginated task list for a project."""
    _, _, project_id_s, page_s = callback.data.split(":")
    ok = await _render_task_list(callback.message, api, int(project_id_s), int(page_s))
    if not ok:
        await callback.answer("Не удалось загрузить задачи", show_alert=True)
        return
    await callback.answer()


# ------------------------------------------------------------- inline: card
def _parse_task_callback(data: str) -> tuple[int, int, int]:
    """Parse '{action}:{task_id}:{project_id}:{page}' callback payloads."""
    _, _, task_id, project_id, page = data.split(":")
    return int(task_id), int(project_id), int(page)


@router.callback_query(F.data.startswith("task:view:"))
async def cb_view_task(callback: CallbackQuery, api: UserApi) -> None:
    """Show a task card with actions."""
    task_id, project_id, page = _parse_task_callback(callback.data)
    try:
        task = await api.get_task(task_id)
    except ApiError:
        await callback.answer("Задача не найдена", show_alert=True)
        return
    await callback.message.edit_text(
        _task_card(task), reply_markup=task_actions_keyboard(task_id, project_id, page)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:status:"))
async def cb_set_status(callback: CallbackQuery, api: UserApi) -> None:
    """Change the task status and re-render its card."""
    _, _, task_id_s, new_status, project_id_s, page_s = callback.data.split(":")
    task_id, project_id, page = int(task_id_s), int(project_id_s), int(page_s)
    try:
        task = await api.update_task(task_id, status=new_status)
    except ApiError:
        await callback.answer("Не удалось обновить статус", show_alert=True)
        return
    await callback.message.edit_text(
        _task_card(task), reply_markup=task_actions_keyboard(task_id, project_id, page)
    )
    await callback.answer(f"Статус: {STATUS_LABEL[task['status']]}")


@router.callback_query(F.data.startswith("task:del:"))
async def cb_delete_confirm(callback: CallbackQuery) -> None:
    """Ask for confirmation before deleting a task."""
    task_id, project_id, page = _parse_task_callback(callback.data)
    await callback.message.edit_text(
        "🗑 Удалить задачу?",
        reply_markup=confirm_task_delete_keyboard(task_id, project_id, page),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:delyes:"))
async def cb_delete_task(callback: CallbackQuery, api: UserApi) -> None:
    """Delete the task after confirmation and return to the list."""
    task_id, project_id, page = _parse_task_callback(callback.data)
    try:
        await api.delete_task(task_id)
    except ApiError:
        await callback.answer("Не удалось удалить задачу", show_alert=True)
        return
    await _render_task_list(callback.message, api, project_id, page)
    await callback.answer("Задача удалена")
