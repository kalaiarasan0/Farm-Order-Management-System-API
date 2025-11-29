# Farmai - FastAPI Application

A modern FastAPI application template for building scalable APIs.

## Features

- ✅ FastAPI framework with async/await support
- ✅ Pydantic for request/response validation
- ✅ SQLAlchemy for ORM (ready to extend)
- ✅ Environment configuration management
- ✅ Comprehensive test setup with pytest
- ✅ Code quality tools (black, isort, flake8, mypy)
- ✅ CORS middleware configured
- ✅ Health check endpoint

## Project Structure

```
farmai/
├── app/
│   ├── api/              # API route handlers
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── config.py         # Configuration
│   └── main.py           # Application factory
├── tests/                # Test suite
├── .github/
│   └── copilot-instructions.md
├── .env.example          # Environment variables template
├── pyproject.toml        # Project configuration
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 2. Set Up Environment

```bash
cp .env.example .env
```

### 3. Run Development Server

```bash
python -m app.main
```

Server runs at `http://localhost:8000`

### 4. API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 5. Run Tests

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app
```

## Development

### Code Formatting

```bash
black app tests
isort app tests
```

### Linting

```bash
flake8 app tests
mypy app
```

### Run All Checks

```bash
black app tests && isort app tests && flake8 app tests && mypy app && pytest
```

## Configuration

Environment variables are loaded from `.env` file using `pydantic-settings`:

- `DEBUG`: Enable debug mode (default: False)
- `LOG_LEVEL`: Logging level (default: INFO)
- `DATABASE_URL`: Database connection string
- `HOST`: Server host (default: 127.0.0.1 — binds to localhost only). Set to `0.0.0.0` in `.env` to allow external access (e.g., running in Docker or when accessing from another machine).
- `PORT`: Server port (default: 8000)

## Adding New Features

### Adding API Routes

1. Create handler in `app/api/` directory
2. Include router in `app/main.py`
3. Define schemas in `app/schemas/`
4. Add tests in `tests/`

### Adding Services

Business logic goes in `app/services/` and is called from API handlers.

### Adding Models

Database models go in `app/models/` using SQLAlchemy.

## License

MIT


### Alembic comments to migrate
alembic revision --autogenerate -m "file name" - suffix
alembic heads
alembic upgrade head
alembic current
alembic history
