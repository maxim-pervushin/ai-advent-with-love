# FastAPI TODO List API

A simple TODO list API built with FastAPI and SQLite.

## Features

- Create, Read, Update, and Delete (CRUD) operations for TODO items
- SQLite database for data persistence
- Docker support for easy deployment
- Interactive API documentation

## Prerequisites

- Python 3.7+
- Docker (optional, for containerization)
- Docker Compose (optional, for containerization)

## Installation

### Without Docker

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

5. Access the API at `http://localhost:8000`

### With Docker

1. Build and run with Docker:
   ```bash
   docker build -t todo-api .
   docker run -p 8000:8000 todo-api
   ```

### With Docker Compose

1. Run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

2. Access the API at `http://localhost:8000`

## API Documentation

- Interactive API documentation: `http://localhost:8000/docs`
- Alternative API documentation: `http://localhost:8000/redoc`

## API Endpoints

- `GET /` - Welcome message and API information
- `GET /todos` - Get all TODO items
- `GET /todos/{id}` - Get a specific TODO item
- `POST /todos` - Create a new TODO item
- `PUT /todos/{id}` - Update an existing TODO item
- `DELETE /todos/{id}` - Delete a TODO item

## Project Structure

```
.
├── main.py          # Main FastAPI application
├── requirements.txt # Python dependencies
├── Dockerfile      # Docker configuration
├── docker-compose.yml # Docker Compose configuration
├── todos.db         # SQLite database (created automatically)
└── README.md        # This file