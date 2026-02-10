from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os

# Initialize FastAPI app
app = FastAPI(title="TODO API", description="A simple TODO list API with FastAPI and SQLite")

# Database setup
DB_NAME = "/app/data/todos.db"

def init_db():
    """Initialize the database with a todos table if it doesn't exist"""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models for request/response validation
class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class Todo(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool

    class Config:
        from_attributes = True

# API routes
@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {"message": "Welcome to the TODO API", "docs": "/docs"}

@app.get("/todos", response_model=List[Todo])
def get_todos():
    """Get all todos"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, completed FROM todos")
    todos = cursor.fetchall()
    conn.close()
    
    return [
        Todo(
            id=todo[0],
            title=todo[1],
            description=todo[2],
            completed=bool(todo[3])
        ) for todo in todos
    ]

@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    """Get a specific todo by ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, completed FROM todos WHERE id = ?", (todo_id,))
    todo = cursor.fetchone()
    conn.close()
    
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return Todo(
        id=todo[0],
        title=todo[1],
        description=todo[2],
        completed=bool(todo[3])
    )

@app.post("/todos", response_model=Todo)
def create_todo(todo: TodoCreate):
    """Create a new todo"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO todos (title, description, completed) VALUES (?, ?, ?)",
        (todo.title, todo.description, False)
    )
    todo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return Todo(
        id=todo_id,
        title=todo.title,
        description=todo.description,
        completed=False
    )

@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo_update: TodoUpdate):
    """Update an existing todo"""
    # First check if todo exists
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, completed FROM todos WHERE id = ?", (todo_id,))
    existing_todo = cursor.fetchone()
    
    if not existing_todo:
        conn.close()
        raise HTTPException(status_code=404, detail="Todo not found")
    
    # Update fields if provided
    title = todo_update.title if todo_update.title is not None else existing_todo[1]
    description = todo_update.description if todo_update.description is not None else existing_todo[2]
    completed = todo_update.completed if todo_update.completed is not None else bool(existing_todo[3])
    
    cursor.execute(
        "UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?",
        (title, description, completed, todo_id)
    )
    conn.commit()
    conn.close()
    
    return Todo(
        id=todo_id,
        title=title,
        description=description,
        completed=completed
    )

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    """Delete a todo"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return {"message": "Todo deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)