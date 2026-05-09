from __future__ import annotations

from fastapi.responses import JSONResponse


def openai_error(
    message: str,
    *,
    status_code: int = 400,
    param: str | None = None,
    code: str | None = None,
    error_type: str = "invalid_request_error",
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": message,
                "type": error_type,
                "param": param,
                "code": code,
            }
        },
    )
