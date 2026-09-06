"""Application errors → HTTP responses, registered once on the app.

Keeps routes free of `try/except` and gives every failure the same body shape as
FastAPI's own `HTTPException` (`{"detail": ...}`), so one client parser covers both.
"""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

from source_service.application.errors import SourceAlreadyExistsError, SourceNotRelevantError

STATUS_BY_ERROR: dict[type[Exception], int] = {
    SourceAlreadyExistsError: status.HTTP_409_CONFLICT,
    SourceNotRelevantError: status.HTTP_422_UNPROCESSABLE_ENTITY,
}


def _responder(http_status: int) -> Callable[[Request, Exception], Awaitable[Response]]:
    async def respond(_: Request, error: Exception) -> Response:
        return JSONResponse(status_code=http_status, content={"detail": str(error)})

    return respond


def install_error_handlers(app: FastAPI) -> None:
    for error_type, http_status in STATUS_BY_ERROR.items():
        app.add_exception_handler(error_type, _responder(http_status))
