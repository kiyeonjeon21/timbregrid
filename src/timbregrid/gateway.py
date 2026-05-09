from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from pydantic import ValidationError

from timbregrid.adapters.base import AdapterDependencyError
from timbregrid.errors import openai_error
from timbregrid.models import SpeechRequest
from timbregrid.registry import get_adapter
from timbregrid.routing import RouteNotFound, resolve_route


SUPPORTED_OUTPUT_FORMATS = {"mp3", "wav", "pcm"}


def create_app(default_model: str = "fake:tts") -> FastAPI:
    app = FastAPI(title="TimbreGrid", version="0.1.0")

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(_: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        param = ".".join(str(part) for part in first.get("loc", [])[1:])
        return openai_error(
            first.get("msg", "Invalid request"),
            status_code=400,
            param=param or None,
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "model": default_model}

    @app.post("/v1/audio/speech")
    async def create_speech(payload: dict[str, Any]) -> Response:
        try:
            request = SpeechRequest.model_validate(payload)
        except ValidationError as exc:
            first = exc.errors()[0]
            param = ".".join(str(part) for part in first.get("loc", []))
            return openai_error(
                first.get("msg", "Invalid request"),
                status_code=400,
                param=param or None,
            )

        if request.stream_format == "sse":
            return openai_error(
                "stream_format='sse' is not supported by this model",
                param="stream_format",
                code="unsupported_stream_format",
            )

        if request.response_format not in SUPPORTED_OUTPUT_FORMATS:
            return openai_error(
                f"response_format '{request.response_format}' is not supported by the MVP gateway",
                param="response_format",
                code="unsupported_response_format",
            )

        try:
            route = resolve_route(request, default_model=default_model)
        except RouteNotFound as exc:
            return openai_error(
                str(exc),
                param="model",
                code="no_route_found",
            )

        selected_model = route.selected_model
        routed_request = request.model_copy(update={"model": selected_model})

        try:
            adapter = get_adapter(selected_model)
        except KeyError:
            return openai_error(
                f"Model '{selected_model}' was not found",
                status_code=404,
                param="model",
                code="model_not_found",
            )

        try:
            result = adapter.synthesize(routed_request)
        except AdapterDependencyError as exc:
            return openai_error(
                str(exc),
                status_code=503,
                param="model",
                code="adapter_dependency_missing",
            )
        except ValueError as exc:
            return openai_error(str(exc))

        return Response(
            content=result.audio,
            media_type="application/octet-stream",
            headers={
                "X-TimbreGrid-Model": result.model,
                "X-TimbreGrid-Route-Reason": route.reason,
                "X-TimbreGrid-Audio-Format": result.format,
                "X-TimbreGrid-Sample-Rate": str(result.sample_rate_hz),
            },
        )

    return app


app = create_app()
