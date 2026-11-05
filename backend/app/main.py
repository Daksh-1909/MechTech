from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes.system import router as system_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.core.paths import ensure_data_directories


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    ensure_data_directories()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="MechTech - Detect. Diagnose. Maintain.",
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
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
