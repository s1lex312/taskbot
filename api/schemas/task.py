"""Task schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from api.models.enums import TaskPriority, TaskStatus

# The bot renders descriptions inside Telegram messages (4096-char limit),
# so the API caps them well below that ceiling.
MAX_DESCRIPTION_LENGTH = 2000


class TaskCreate(BaseModel):
    """Payload for creating a task."""

    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date | None = None


class TaskUpdate(BaseModel):
    """Payload for a partial task update. Unset fields stay untouched."""

    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None


class TaskRead(BaseModel):
    """Public representation of a task."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    created_at: datetime
    updated_at: datetime
