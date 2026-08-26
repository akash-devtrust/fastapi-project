# Simple FastAPI Todo API

A small, beginner-friendly REST API built with Python, FastAPI, and MySQL. It stores todos in a MySQL database, so data stays saved after the server restarts.

## Project Structure

```text
fastapi-project/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── db_models.py
│   ├── main.py
│   └── models.py
├── .gitignore
├── requirements.txt
├── README.md
└── .env.example
```

## Create and Activate a Virtual Environment

From inside the `fastapi-project` directory:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Set Up MySQL

Create a MySQL database for the project:

```sql
CREATE DATABASE fastapi_todos;
```

Create a local `.env` file from the example file:

```bash
cp .env.example .env
```

Then update `.env` with your MySQL username and password:

```env
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/fastapi_todos
```

Example for a local MySQL root user:

```env
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/fastapi_todos
```

The app will create the `todos` table automatically when it starts.

## Run the API

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

## Available Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Welcome message |
| GET | `/health` | API health status |
| GET | `/todos` | Get all todos |
| GET | `/todos/{todo_id}` | Get one todo |
| POST | `/todos` | Create a todo |
| PUT | `/todos/{todo_id}` | Update a todo |
| DELETE | `/todos/{todo_id}` | Delete a todo |

## Test the API

Open a second terminal while the server is running.

### Welcome Message

```bash
curl http://127.0.0.1:8000/
```

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

### Create a Todo

```bash
curl -X POST http://127.0.0.1:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"Learn FastAPI","description":"Build a simple Todo API","completed":false}'
```

### Get All Todos

```bash
curl http://127.0.0.1:8000/todos
```

### Get One Todo

```bash
curl http://127.0.0.1:8000/todos/1
```

### Update a Todo

```bash
curl -X PUT http://127.0.0.1:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"title":"Learn FastAPI","description":"Update the Todo API","completed":true}'
```

### Delete a Todo

```bash
curl -X DELETE http://127.0.0.1:8000/todos/1
```

### Confirm Deleted Todo Returns 404

```bash
curl http://127.0.0.1:8000/todos/1
```

## Initialize Git

```bash
git init
git add .
git commit -m "Create simple FastAPI Todo API"
```

## Push to GitHub

Create a new empty repository on GitHub first. Then run:

```bash
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

## Server Deployment

On the server, pull the latest code:

```bash
cd ~/fastapi-project
git pull origin main
```

Then reload the ASGI website:

```bash
pa website reload --domain kinady.pythonanywhere.com
```
