from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes.system import router as system_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.core.paths import ensure_data_directories
from app.db.base import Base
from app.db.session import engine, SessionLocal
import app.models  # noqa: F401

logger = logging.getLogger(__name__)


def init_database() -> None:
    """Ensure data directories, database tables, and default demo seed data exist."""
    ensure_data_directories()
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logger.warning("Base.metadata.create_all encountered an exception: %s", exc)

    with SessionLocal() as db:
        from app.models.user import User
        try:
            if db.query(User).first() is None:
                from scripts.seed_demo_data import seed_demo
                logger.info("Empty database detected. Seeding demonstration data...")
                seed_demo(db)
        except Exception as exc:
            logger.warning("Auto-seed demo data encountered an exception: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    init_database()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="MechTech - Detect. Diagnose. Maintain.",
        lifespan=lifespan,
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(system_router)
    app.include_router(system_router, prefix=settings.api_v1_prefix)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
