from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class TodoBase(BaseModel):
    title: str
    description: str | None = None
    completed: bool = False
    priority: Literal["low", "medium", "high"] = "medium"
    due_date: date | None = None


class TodoCreate(TodoBase):
    pass


class TodoUpdate(TodoBase):
    pass


class Todo(TodoBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TodoPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None
    priority: Literal["low", "medium", "high"] | None = None
    due_date: date | None = None
