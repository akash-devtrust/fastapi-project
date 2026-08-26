from fastapi import FastAPI, HTTPException, Response, status

from app.models import Todo, TodoCreate, TodoUpdate

app = FastAPI(title="Simple Todo API")

todos: list[Todo] = []


def get_next_id() -> int:
    if not todos:
        return 1
    return max(todo.id for todo in todos) + 1


def find_todo(todo_id: int) -> Todo:
    for todo in todos:
        if todo.id == todo_id:
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
def get_todos(search: str | None = None, completed : bool | None = None) -> list[Todo]:
    results = todos
    if search is not None:
        search_text = search.lower()
        results = [
            todo
            for todo in results
            if search_text in todo.title.lower()
            or (
                todo.description is not None and search_text in todo.description.lower()
            )
        ]
    if completed is not None:
        results = [
            todo
            for todo in results
            if todo.completed == completed
        ]
    return results


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int) -> Todo:
    return find_todo(todo_id)


@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(todo_data: TodoCreate) -> Todo:
    todo = Todo(id=get_next_id(), **todo_data.model_dump())
    todos.append(todo)
    return todo


@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo_data: TodoUpdate) -> Todo:
    existing_todo = find_todo(todo_id)
    updated_todo = Todo(id=existing_todo.id, **todo_data.model_dump())

    todo_index = todos.index(existing_todo)
    todos[todo_index] = updated_todo

    return updated_todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int) -> Response:
    todo = find_todo(todo_id)
    todos.remove(todo)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
