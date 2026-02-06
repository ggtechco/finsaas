"""FastAPI application for the FinSaaS web dashboard."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from finsaas.web import STATIC_DIR, UPLOAD_DIR
from finsaas.web.routes import backtest, data, optimize, strategies


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # Import example strategies so they register
    import finsaas.strategy.examples  # noqa: F401
    yield


def _get_cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "*")
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def create_app() -> FastAPI:
    app = FastAPI(
        title="FinSaaS Dashboard",
        description="Backtest & Parameter Optimization Engine",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_cors_origins(),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health_check() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    app.include_router(strategies.router, prefix="/api")
    app.include_router(data.router, prefix="/api")
    app.include_router(backtest.router, prefix="/api")
    app.include_router(optimize.router, prefix="/api")

    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


app = create_app()
