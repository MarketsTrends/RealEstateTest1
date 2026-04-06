from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    pass


class DatabaseUnavailableError(DomainError):
    pass


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
