from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.db_models import TodoDB
from app.models import Todo, TodoCreate, TodoUpdate

app = FastAPI(title="Simple Todo API")

Base.metadata.create_all(bind=engine)


def find_todo(todo_id: int, db: Session) -> TodoDB:
    todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if todo is not None:
        return todo

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Todo not found",
    )


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to the Simple Todo API"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/todos", response_model=list[Todo])
def get_todos(
    search: str | None = None,
    completed: bool | None = None,
    priority: Literal["low", "medium", "high"] | None = None,
    db: Session = Depends(get_db),
) -> list[TodoDB]:
    query = db.query(TodoDB)

    if search is not None:
        search_text = f"%{search}%"
        query = query.filter(
            (TodoDB.title.ilike(search_text))
            | (TodoDB.description.ilike(search_text))
        )
    if priority is not None:
        query = query.filter(TodoDB.priority == priority)

    if completed is not None:
        query = query.filter(TodoDB.completed == completed)

    return query.all()


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int, db: Session = Depends(get_db)) -> TodoDB:
    return find_todo(todo_id, db)


@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(todo_data: TodoCreate, db: Session = Depends(get_db)) -> TodoDB:
    todo = TodoDB(**todo_data.model_dump())
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(
    todo_id: int,
    todo_data: TodoUpdate,
    db: Session = Depends(get_db),
) -> TodoDB:
    todo = find_todo(todo_id, db)
    todo.title = todo_data.title
    todo.description = todo_data.description
    todo.completed = todo_data.completed
    todo.priority = todo_data.priority

    db.commit()
    db.refresh(todo)

    return todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db)) -> Response:
    todo = find_todo(todo_id, db)
    db.delete(todo)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
