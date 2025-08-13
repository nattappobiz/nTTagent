"""FastAPI application entry point.

This module sets up the FastAPI application, configures logging, initialises
the database and registers all routers. When running via ``uvicorn``, the
application object defined here will be automatically discovered.
"""

from __future__ import annotations

import logging
from fastapi import FastAPI

from app.config import setup_logging
from app.models.database import init_db
from app.routes import uploads, citizens, files, export


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    setup_logging()
    init_db()
    app = FastAPI(title="Elderdocs API", version="1.0.0")
    # Register routers
    app.include_router(uploads.router, tags=["uploads"])
    app.include_router(citizens.router, tags=["citizens"])
    app.include_router(files.router, tags=["files"])
    app.include_router(export.router, tags=["export"])

    # Add a root endpoint
    @app.get("/")
    def read_root():
        return {"message": "Welcome to Elderdocs API"}

    return app


app = create_app()