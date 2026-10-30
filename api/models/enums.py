"""Domain enumerations."""

from enum import StrEnum


class TaskStatus(StrEnum):
    """Lifecycle states of a task."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(StrEnum):
    """Priority levels of a task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
