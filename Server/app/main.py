"""TerraSense NER — FastAPI application entrypoint.

Wires together configuration, logging, CORS, routers and error handling.
Contains no business logic — that lives in the service layer.

Run:  uvicorn app.main:app --reload
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.models.common import ErrorDetail, ErrorResponse

configure_logging()
logger = logging.getLogger("terrasense")
settings = get_settings()

# Map HTTP status codes to stable, machine-readable error codes.
_ERROR_CODE_BY_STATUS = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_ERROR",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Log startup/shutdown so operators can confirm the service state."""
    logger.info(
        "Starting %s v%s (env=%s, prefix=%s)",
        settings.app_name,
        settings.version,
        settings.environment,
        settings.api_prefix,
    )
    logger.info("CORS allowed origins: %s", ", ".join(settings.backend_cors_origins) or "(none)")
    yield
    logger.info("Shutting down %s", settings.app_name)


def _error_response(status_code: int, message: str, code: str | None = None) -> JSONResponse:
    """Build the standard `{ "error": { code, message } }` envelope."""
    resolved_code = code or _ERROR_CODE_BY_STATUS.get(status_code, "ERROR")
    body = ErrorResponse(error=ErrorDetail(code=resolved_code, message=message))
    return JSONResponse(status_code=status_code, content=body.model_dump())


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )

    # --- CORS (React/Vite frontend) ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Lightweight request logging with timing ---
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %d (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    # --- Consistent error envelopes ---
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return _error_response(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
        return _error_response(422, "Request validation failed.", code="VALIDATION_ERROR")

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s", request.url.path)
        return _error_response(500, "An unexpected error occurred.", code="INTERNAL_ERROR")

    # --- Routes ---
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/", tags=["Meta"], summary="Service info")
    def root() -> dict:
        """Root pointer to the API and docs."""
        return {
            "service": settings.app_name,
            "version": settings.version,
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health",
        }

    return app


app = create_app()
