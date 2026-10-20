"""App factory. Run with: uvicorn app.main:app --reload"""
import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, health, urls
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.db.database import check_connection, make_engine
from app.core.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    settings = get_settings()
    if len(settings.jwt_secret) < 32:
        raise RuntimeError("JWT_SECRET must be set to a random string of at least 32 characters.")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = make_engine(settings.database_url)
        check_connection(app.state.engine)
        logger.info("Database connected successfully")
        yield
        app.state.engine.dispose()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.rate_limiter = RateLimiter()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error("Request failed: %s", exc.message)
        elif exc.status_code == 429:
            client = request.client.host if request.client else "unknown"
            logger.warning("Rate limited %s %s from %s", request.method, request.url.path, client)
        return JSONResponse(
            status_code=exc.status_code, content={"detail": exc.message}, headers=exc.headers
        )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(urls.router)
    app.include_router(urls.redirect_router)  # catch-all, keep last
    return app


app = create_app()