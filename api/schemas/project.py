"""Project schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    """Payload for creating a project."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectUpdate(BaseModel):
    """Payload for a partial project update. Unset fields stay untouched."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class ProjectRead(BaseModel):
    """Public representation of a project."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: datetime
