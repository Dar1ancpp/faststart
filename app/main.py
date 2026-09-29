import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.config import get_settings
from app.routers import api_router, router, static_files, templates
from app.routers.game_api import game_api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import ensure_db_and_tables

    ensure_db_and_tables()
    yield


app = FastAPI(
    middleware=[
        Middleware(SessionMiddleware, secret_key=get_settings().secret_key)
    ],
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(api_router)
app.include_router(game_api_router)
app.mount("/static", static_files, name="static")


@app.middleware("http")
async def recover_uninitialized_db(request: Request, call_next):
    """If a request hits a missing schema, create tables once and retry."""
    from app.database import recover_if_uninitialized

    try:
        return await call_next(request)
    except Exception as exc:
        if not recover_if_uninitialized(exc):
            raise
        logger.info("Retrying %s after database init", request.url.path)
        try:
            return await call_next(request)
        except Exception:
            if request.method.upper() == "GET":
                return RedirectResponse(url=str(request.url), status_code=303)
            raise


@app.get("/health")
async def health():
    return {"ok": True}


@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_redirect_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/api") or "application/json" in request.headers.get("accept", "") or request.headers.get("authorization"):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": getattr(exc, "detail", "Could not validate credentials")},
        )
    return templates.TemplateResponse(
        request=request,
        name="401.html",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=get_settings().app_host,
        port=get_settings().app_port,
        reload=get_settings().env.lower() != "production",
    )
