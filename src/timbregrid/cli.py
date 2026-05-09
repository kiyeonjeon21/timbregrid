from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

import typer

from timbregrid.bench import run_benchmark, write_benchmark
from timbregrid.conformance import run_conformance, write_conformance_report
from timbregrid.gateway import create_app
from timbregrid.manifest import ManifestError, load_manifest
from timbregrid.registry import get_model_entry, list_models


app = typer.Typer(help="TimbreGrid compatibility and evaluation tools.")
manifest_app = typer.Typer(help="Validate and inspect model manifests.")
models_app = typer.Typer(help="List and inspect known TTS models.")


@manifest_app.command("validate")
def validate_manifest(path: Annotated[Path, typer.Argument(exists=True, dir_okay=False)]) -> None:
    try:
        manifest = load_manifest(path)
    except ManifestError as exc:
        typer.echo(f"Invalid manifest: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"OK {path} ({manifest.id})")


@app.command()
def bench(
    model: Annotated[str, typer.Argument()],
    suite: Annotated[str, typer.Option("--suite")] = "realtime-agent",
    voice: Annotated[str | None, typer.Option("--voice")] = None,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    output_format: Annotated[str, typer.Option("--format")] = "json",
) -> None:
    if output_format != "json":
        typer.echo("Only --format json is supported in the MVP", err=True)
        raise typer.Exit(1)

    try:
        result = run_benchmark(model, suite=suite, voice=voice)
    except (KeyError, RuntimeError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    if output is not None:
        write_benchmark(result, output)
        typer.echo(f"Wrote {output}")
    else:
        typer.echo(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))


@models_app.command("list")
def list_known_models() -> None:
    for model in list_models():
        executable = "executable" if model.executable else "manifest-only"
        typer.echo(f"{model.id}\t{executable}\t{model.status}")


@models_app.command("inspect")
def inspect_model(model: Annotated[str, typer.Argument()]) -> None:
    try:
        entry = get_model_entry(model)
    except KeyError as exc:
        typer.echo(f"Unknown model: {model}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(json.dumps(entry.to_dict(), indent=2, sort_keys=True))


@app.command()
def conformance(
    base_url: Annotated[str, typer.Argument()],
    endpoint: Annotated[str, typer.Option("--endpoint")] = "audio.speech",
    model: Annotated[str, typer.Option("--model")] = "fake:tts",
    voice: Annotated[str, typer.Option("--voice")] = "alloy",
    response_format: Annotated[str, typer.Option("--response-format")] = "wav",
    timeout: Annotated[float, typer.Option("--timeout")] = 10.0,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    try:
        result = run_conformance(
            base_url,
            endpoint=endpoint,
            model=model,
            voice=voice,
            response_format=response_format,
            timeout=timeout,
        )
    except Exception as exc:
        typer.echo(f"Conformance failed: {exc}", err=True)
        raise typer.Exit(1) from exc

    if output is not None:
        write_conformance_report(result, output)
        typer.echo(f"Wrote {output}")

    if result.ok:
        typer.echo(f"OK {result.passed}/{result.summary['total']} conformance cases passed")
        return

    for failure in result.failures:
        typer.echo(f"FAIL {failure}", err=True)
    raise typer.Exit(1)


@app.command()
def serve(
    model: Annotated[str | None, typer.Option("--model")] = None,
    host: Annotated[str | None, typer.Option("--host")] = None,
    port: Annotated[int | None, typer.Option("--port")] = None,
) -> None:
    import uvicorn

    try:
        resolved_model, resolved_host, resolved_port = resolve_serve_config(model, host, port)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    uvicorn.run(create_app(default_model=resolved_model), host=resolved_host, port=resolved_port)


def resolve_serve_config(
    model: str | None = None,
    host: str | None = None,
    port: int | None = None,
) -> tuple[str, str, int]:
    resolved_model = model or os.environ.get("TIMBREGRID_MODEL") or "fake:tts"
    resolved_host = host or os.environ.get("TIMBREGRID_HOST") or "127.0.0.1"
    resolved_port = port if port is not None else _env_port()
    return resolved_model, resolved_host, resolved_port


def _env_port() -> int:
    raw = os.environ.get("TIMBREGRID_PORT")
    if raw is None or raw == "":
        return 8889
    try:
        port = int(raw)
    except ValueError as exc:
        raise ValueError("TIMBREGRID_PORT must be an integer") from exc
    if port <= 0 or port > 65535:
        raise ValueError("TIMBREGRID_PORT must be between 1 and 65535")
    return port


app.add_typer(manifest_app, name="manifest")
app.add_typer(models_app, name="models")


if __name__ == "__main__":
    app()
