<!-- Farmai FastAPI Project - Copilot Instructions -->

# Farmai FastAPI Project

## Project Overview

Farmai is a modern FastAPI application template designed for building scalable, type-safe APIs. The project uses async/await patterns, Pydantic for validation, and SQLAlchemy for persistence.

## Architecture

### Core Structure

- **`app/main.py`**: Application factory that creates and configures the FastAPI instance with middleware (CORS), router includes, and settings
- **`app/config.py`**: Centralized settings using `pydantic-settings` for environment variable management
- **`app/api/`**: Route handlers organized by feature (e.g., `health.py`, `users.py`, etc.)
- **`app/schemas/`**: Pydantic models for request/response validation
- **`app/models/`**: SQLAlchemy ORM models for database tables
- **`app/services/`**: Business logic layer called from route handlers

### Data Flow

Routes (`app/api/`) → Services (`app/services/`) → Models (`app/models/`) → Database

Routes validate input using schemas and call service functions. Services contain business logic and interact with database models.

## Key Conventions

### API Route Organization

- All routes defined in `app/api/` modules
- Each module uses `APIRouter` with a prefix: `router = APIRouter(prefix="/api/v1/resource")`
- Routes are included in `main.py` with `app.include_router()`
- Use async functions: `async def endpoint() -> dict | list | Model:`

Example:
```python
# app/api/users.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/")
async def list_users() -> list[UserSchema]:
    return await service.get_all_users()
```

### Schema Definition

- Request/response models in `app/schemas/` as Pydantic `BaseModel` classes
- Name schemas with domain (e.g., `UserCreate`, `UserResponse`)
- Include docstrings for fields using `Field(description="...")`

### Service Layer Pattern

- Services in `app/services/` contain business logic
- Services accept validated data from schemas
- Services return data suitable for response schemas
- Use async functions to leverage database async drivers

### Environment Configuration

- Load from `.env` using `pydantic-settings`
- Define in `app/config.py` as `Settings` class
- Access via `from app.config import settings`
- Provide `.env.example` template for developers

## Development Workflows

### Setup

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
```

### Running

```bash
# Start dev server (auto-reload)
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --log-level info
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py -v
```

### Code Quality

```bash
# Format code (required before commit)
black app tests
isort app tests

# Check linting
flake8 app tests

# Type checking
mypy app

# Run all checks (test + lint + format)
pytest && black app tests && isort app tests && flake8 app tests && mypy app
```

## Integration Points

### Database

- SQLAlchemy sessions created per request (implement middleware in `app/middleware/`)
- Models inherit from declarative base
- Async support via `sqlalchemy.ext.asyncio` for production

### External APIs

- Use `httpx` for async HTTP requests (installed with dev dependencies)
- Define API clients in `app/services/` or dedicated `app/integrations/` module
- Mock in tests using `pytest-httpx` or `responses`

### Middleware

- CORS configured in `app/main.py` (origins currently allow all - restrict in production)
- Add middleware via `app.add_middleware(MiddlewareClass, **kwargs)`

## Common Patterns

### Adding a New Feature

1. Create schema in `app/schemas/` for request/response
2. Create service in `app/services/` for business logic
3. Create route in `app/api/` that calls service and returns schema
4. Include router in `app/main.py`: `app.include_router(router)`
5. Add tests in `tests/test_*.py`

### Error Handling

```python
from fastapi import HTTPException

@router.get("/{id}")
async def get_resource(id: int):
    resource = await service.get_by_id(id)
    if not resource:
        raise HTTPException(status_code=404, detail="Not found")
    return resource
```

### Authentication (Future Extension)

- Implement as middleware or dependency in `app/dependencies.py`
- Use FastAPI's `Depends()` for route protection
- JWT tokens recommended with `python-jose`

## Testing Strategy

- **`tests/conftest.py`**: Test fixtures (TestClient, database sessions)
- **`tests/test_*.py`**: Test modules organized by feature
- Use `TestClient` from FastAPI for endpoint testing
- Mock services in unit tests; use test database for integration tests
- Async tests automatically handled by `pytest-asyncio` (config in `pyproject.toml`)

## Tools & Quality Standards

- **Formatter**: Black (100 char line length)
- **Import sorting**: isort with Black profile
- **Linter**: flake8
- **Type checking**: mypy (strict mode disabled by default)
- **Testing**: pytest with async support
- **Dependencies**: Locked in `pyproject.toml` with version ranges

## Key Files Reference

| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies, tool config, build settings |
| `.env.example` | Template for environment variables |
| `app/main.py` | Application factory and server entry point |
| `app/config.py` | Settings management |
| `app/api/` | API route handlers |
| `tests/conftest.py` | Test fixtures |
