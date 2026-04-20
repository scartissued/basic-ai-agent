# FastAPI MVC Backend

A basic FastAPI backend with MVC structure using `uv` as the package manager.

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── main.py            # FastAPI app entry point
│   ├── controllers/       # API route handlers
│   │   ├── __init__.py
│   │   └── item_controller.py
│   ├── models/            # Data models
│   │   ├── __init__.py
│   │   └── item.py
│   ├── schemas/           # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   └── item.py
│   └── services/          # Business logic
│       ├── __init__.py
│       └── item_service.py
├── pyproject.toml         # Project configuration & dependencies
├── run.sh                 # Development server script
└── run_prod.sh            # Production server script
```

## Setup

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install dependencies

```bash
uv sync
```

## Running the Server

### Development (with auto-reload)

uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

### Production

uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /items` - List all items
- `GET /items/{id}` - Get item by ID
- `POST /items` - Create new item
- `PUT /items/{id}` - Update item
- `DELETE /items/{id}` - Delete item

## Interactive API Docs

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Commands

```bash
# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Format code
uv run ruff format .
```
