"""Project handlers: /projects, /new_project, inline project card."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.utils import answer_api_error, esc
from bot.keyboards.projects import (
    confirm_delete_keyboard,
    project_actions_keyboard,
    projects_keyboard,
)
from bot.services.api_client import ApiError, UserApi
from bot.states.forms import NewProjectForm

logger = logging.getLogger(__name__)

router = Router(name="projects")


def _project_card(project: dict) -> str:
    """Render a project as an HTML card."""
    description = project.get("description") or "—"
    created = project["created_at"][:10]
    return f"📁 <b>{esc(project['name'])}</b>\n\n" f"{esc(description)}\n\n" f"🗓 Создан: {created}"


# ------------------------------------------------------------------ /projects
@router.message(Command("projects"))
async def cmd_projects(message: Message, api: UserApi) -> None:
    """List the user's projects with inline buttons."""
    try:
        projects = await api.list_projects()
    except ApiError as exc:
        await answer_api_error(message, exc)
        return

    if not projects:
        await message.answer("Проектов пока нет. Создай первый: /new_project")
        return
    await message.answer("Твои проекты:", reply_markup=projects_keyboard(projects))


# --------------------------------------------------------------- /new_project
@router.message(Command("new_project"))
async def cmd_new_project(message: Message, state: FSMContext) -> None:
    """Start the project-creation FSM."""
    await state.set_state(NewProjectForm.name)
    await message.answer("📁 Название проекта? (до 200 символов)")


@router.message(NewProjectForm.name)
async def np_name(message: Message, state: FSMContext) -> None:
    """Collect the project name."""
    name = (message.text or "").strip()
    if not 1 <= len(name) <= 200:
        await message.answer("Название должно быть от 1 до 200 символов. Ещё раз:")
        return
    await state.update_data(name=name)
    await state.set_state(NewProjectForm.description)
    await message.answer("Описание проекта? Или /skip, чтобы пропустить.")


@router.message(NewProjectForm.description, Command("skip"))
async def np_description_skip(message: Message, state: FSMContext, api: UserApi) -> None:
    """Finish the FSM without a description."""
    await _create_project(message, state, api, description=None)


@router.message(NewProjectForm.description)
async def np_description(message: Message, state: FSMContext, api: UserApi) -> None:
    """Collect the description and finish the FSM."""
    await _create_project(message, state, api, description=(message.text or "").strip())


async def _create_project(
    message: Message, state: FSMContext, api: UserApi, description: str | None
) -> None:
    data = await state.get_data()
    await state.clear()
    try:
        project = await api.create_project(data["name"], description or None)
    except ApiError as exc:
        await answer_api_error(message, exc)
        return
    await message.answer(f"✅ Проект <b>{esc(project['name'])}</b> создан.")


# --------------------------------------------------------------- inline cards
@router.callback_query(F.data.startswith("prj:view:"))
async def cb_view_project(callback: CallbackQuery, api: UserApi) -> None:
    """Show a project card with actions."""
    project_id = int(callback.data.rsplit(":", 1)[1])
    try:
        project = await api.get_project(project_id)
    except ApiError as exc:
        await callback.answer("Проект не найден", show_alert=True)
        logger.info("project %s view failed: %s", project_id, exc)
        return
    await callback.message.edit_text(
        _project_card(project), reply_markup=project_actions_keyboard(project_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prj:del:"))
async def cb_delete_confirm(callback: CallbackQuery) -> None:
    """Ask for confirmation before deleting a project."""
    project_id = int(callback.data.rsplit(":", 1)[1])
    await callback.message.edit_text(
        "🗑 Удалить проект со всеми задачами?",
        reply_markup=confirm_delete_keyboard(project_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prj:delyes:"))
async def cb_delete_project(callback: CallbackQuery, api: UserApi) -> None:
    """Delete the project after confirmation."""
    project_id = int(callback.data.rsplit(":", 1)[1])
    try:
        await api.delete_project(project_id)
    except ApiError:
        await callback.answer("Не удалось удалить проект", show_alert=True)
        return
    await callback.message.edit_text("🗑 Проект удалён.")
    await callback.answer()


@router.callback_query(F.data == "prj:back")
async def cb_back_to_list(callback: CallbackQuery, api: UserApi) -> None:
    """Return to the project list."""
    try:
        projects = await api.list_projects()
    except ApiError as exc:
        await answer_api_error(callback.message, exc)
        await callback.answer()
        return
    if not projects:
        await callback.message.edit_text("Проектов пока нет. Создай первый: /new_project")
    else:
        await callback.message.edit_text("Твои проекты:", reply_markup=projects_keyboard(projects))
    await callback.answer()
