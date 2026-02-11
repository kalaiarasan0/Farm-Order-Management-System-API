"""
FastAPI application main module.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from prometheus_fastapi_instrumentator import Instrumentator
from app.config import settings
from app.api import (
    health,
    orders,
    customers,
    addresses,
    animals,
    inventories,
    ai_work,
    t_animals,
    t_animal_move,
    t_animal_event,
    t_material_management,
    auth,
    dashboard,
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title="Farmai API",
        description="FastAPI application for Farmai",
        version="0.1.0",
        debug=settings.DEBUG,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(orders.router, tags=["orders"])
    app.include_router(customers.router, tags=["customers"])
    app.include_router(addresses.router, tags=["addresses"])
    app.include_router(animals.router, tags=["category"])
    app.include_router(inventories.router, tags=["inventories"])
    app.include_router(ai_work.router, tags=["ai_work"])
    app.include_router(t_animals.router, tags=["t_animals"])
    app.include_router(t_animal_move.router, tags=["t_inventory_animals"])
    app.include_router(t_animal_event.router, tags=["t_animal_events"])
    app.include_router(t_material_management.router, tags=["t_material_management"])
    app.include_router(auth.router)
    app.include_router(dashboard.router)

    #initiate prometheus
    # We do this after including routers so it can label metrics by your route paths
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    
    # Mount static files
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="static")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
