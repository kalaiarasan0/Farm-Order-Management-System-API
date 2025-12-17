"""
FastAPI application main module.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import health, orders, customers, addresses, animals, inventories

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
    app.include_router(animals.router, tags=["products"])
    app.include_router(inventories.router, tags=["inventories"])
    
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
