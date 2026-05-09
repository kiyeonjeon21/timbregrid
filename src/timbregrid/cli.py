from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from timbregrid.bench import run_benchmark, write_benchmark
from timbregrid.conformance import run_conformance, write_conformance_report
from timbregrid.gateway import create_app
from timbregrid.manifest import ManifestError, load_manifest


app = typer.Typer(help="TimbreGrid compatibility and evaluation tools.")
manifest_app = typer.Typer(help="Validate and inspect model manifests.")


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
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    output_format: Annotated[str, typer.Option("--format")] = "json",
) -> None:
    if output_format != "json":
        typer.echo("Only --format json is supported in the MVP", err=True)
        raise typer.Exit(1)

    try:
        result = run_benchmark(model, suite=suite)
    except (KeyError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    if output is not None:
        write_benchmark(result, output)
        typer.echo(f"Wrote {output}")
    else:
        typer.echo(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))


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
    model: Annotated[str, typer.Option("--model")] = "fake:tts",
    host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port")] = 8889,
) -> None:
    import uvicorn

    uvicorn.run(create_app(default_model=model), host=host, port=port)


app.add_typer(manifest_app, name="manifest")


if __name__ == "__main__":
    app()
