"""FastAPI application for knowledge API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import search_router, qa_router, context_router, delegate_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Personal Knowledge API",
        description="API for personal knowledge base access and management",
        version="1.0.0"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
    app.include_router(qa_router, prefix="/api/v1/qa", tags=["Q&A"])
    app.include_router(context_router, prefix="/api/v1/context", tags=["Context"])
    app.include_router(delegate_router, prefix="/api/v1/delegate", tags=["Delegate"])

    @app.get("/")
    def root():
        return {
            "name": "Personal Knowledge API",
            "version": "1.0.0",
            "docs": "/docs"
        }

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    return app
