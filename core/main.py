"""Entry point for running the Gijiroku21 Python Core."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from core.app.api.router import api_router
from core.app.models.response import Envelope, error_response


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gijiroku21 Core",
        description="Local-only transcription backend for Gijiroku21",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_, exc: HTTPException):
        body = error_response(code=str(exc.status_code), message=exc.detail)
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_, exc: Exception):
        body = error_response(code="INTERNAL_ERROR", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    app.include_router(api_router)
    return app


app = create_app()
