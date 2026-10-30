"""FastAPI application entrypoint."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.core.config import get_settings
from api.core.logging import setup_logging
from api.routers import auth, health, projects, tasks, users

logger = logging.getLogger(__name__)


def _error_body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    """Build the unified error payload."""
    return {"error": {"code": code, "message": message, "details": details}}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: configure logging, log startup/shutdown."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("api starting", extra={"environment": settings.environment})
    yield
    logger.info("api stopped")


app = FastAPI(title="Taskbot API", version="1.0.0", lifespan=lifespan)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Render HTTP errors in the unified format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(
            code="http_error",
            message=str(exc.detail),
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Render pydantic validation errors in the unified format."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_body(
            code="validation_error",
            message="Request validation failed",
            details=exc.errors(),
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: log the traceback, return a sanitized 500."""
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body(code="internal_error", message="Internal server error"),
    )


# Unversioned probe for docker/infra checks.
app.include_router(health.router)

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(health.router)
api_v1.include_router(auth.router)
api_v1.include_router(users.router)
api_v1.include_router(projects.router)
api_v1.include_router(tasks.router)
app.include_router(api_v1)
