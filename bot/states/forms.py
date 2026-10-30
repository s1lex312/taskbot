"""FSM state groups for multi-step user input."""

from aiogram.fsm.state import State, StatesGroup


class NewProjectForm(StatesGroup):
    """Steps of the /new_project flow."""

    name = State()
    description = State()
