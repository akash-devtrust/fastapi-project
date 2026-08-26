from datetime import date
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

    class Config:
        from_attributes = True
