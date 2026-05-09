from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

import typer

from timbregrid.bench import run_benchmark, write_benchmark
from timbregrid.benchmark_store import BenchmarkStoreError, validate_benchmark_result
from timbregrid.conformance import run_conformance, write_conformance_report
from timbregrid.gateway import create_app
from timbregrid.manifest import ManifestError, load_manifest
from timbregrid.models import SpeechRequest
from timbregrid.registry import get_model_entry, list_models
from timbregrid.registry_audit import audit_registry
from timbregrid.registry_index import (
    RegistryIndexError,
    stale_registry_artifacts,
    write_registry_artifacts,
)
from timbregrid.routing import RouteNotFound, resolve_route
from timbregrid.voices import VoiceCatalogError


app = typer.Typer(help="TimbreGrid compatibility and evaluation tools.")
manifest_app = typer.Typer(help="Validate and inspect model manifests.")
models_app = typer.Typer(help="List and inspect known TTS models.")
registry_app = typer.Typer(help="Build static registry artifacts.")
route_app = typer.Typer(help="Explain automatic model routing.")


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
    model: Annotated[str, typer.Argument(help="Model id, or 'validate' to validate benchmark JSON.")],
    benchmark_path: Annotated[Path | None, typer.Argument(exists=True, dir_okay=False)] = None,
    suite: Annotated[str, typer.Option("--suite")] = "realtime-agent",
    voice: Annotated[str | None, typer.Option("--voice")] = None,
    hardware_profile: Annotated[str | None, typer.Option("--hardware-profile")] = None,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    output_format: Annotated[str, typer.Option("--format")] = "json",
) -> None:
    if model == "validate":
        if benchmark_path is None:
            typer.echo("Usage: timbregrid bench validate <benchmark.json>", err=True)
            raise typer.Exit(1)
        try:
            result = validate_benchmark_result(benchmark_path)
        except BenchmarkStoreError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc
        typer.echo(f"OK {benchmark_path} ({result.model}, {result.suite})")
        return

    if benchmark_path is not None:
        typer.echo("Unexpected benchmark path. Use: timbregrid bench validate <benchmark.json>", err=True)
        raise typer.Exit(1)

    if output_format != "json":
        typer.echo("Only --format json is supported in the MVP", err=True)
        raise typer.Exit(1)

    try:
        result = run_benchmark(
            model,
            suite=suite,
            voice=voice,
            hardware_profile=hardware_profile,
        )
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


@registry_app.command("build")
def build_registry(
    manifest_dir: Annotated[Path, typer.Option("--manifest-dir")] = Path("manifests"),
    index: Annotated[Path, typer.Option("--index")] = Path("registry/index.json"),
    matrix: Annotated[Path, typer.Option("--matrix")] = Path("docs/support-matrix.md"),
    check: Annotated[bool, typer.Option("--check")] = False,
) -> None:
    try:
        if check:
            stale = stale_registry_artifacts(manifest_dir, index, matrix)
            if stale:
                typer.echo(
                    "Registry artifacts are stale: " + ", ".join(str(path) for path in stale),
                    err=True,
                )
                raise typer.Exit(1)
            typer.echo("OK registry artifacts are current")
            return

        write_registry_artifacts(manifest_dir, index, matrix)
    except RegistryIndexError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Wrote {index}")
    typer.echo(f"Wrote {matrix}")


@registry_app.command("audit")
def audit_registry_command(
    manifest_dir: Annotated[Path, typer.Option("--manifest-dir")] = Path("manifests"),
    timeout: Annotated[float, typer.Option("--timeout", min=0.1)] = 5.0,
    skip_network: Annotated[bool, typer.Option("--skip-network")] = False,
) -> None:
    report = audit_registry(
        manifest_dir,
        check_urls=not skip_network,
        timeout=timeout,
    )
    if not report.ok:
        for issue in report.issues:
            typer.echo(issue.format(), err=True)
        raise typer.Exit(1)

    if skip_network:
        typer.echo(f"OK registry audit passed ({report.manifest_count} manifests, network skipped)")
        return
    typer.echo(
        f"OK registry audit passed ({report.manifest_count} manifests, {report.url_count} URLs checked)"
    )


@route_app.command("explain")
def explain_route(
    model: Annotated[str, typer.Option("--model")] = "auto",
    voice: Annotated[str, typer.Option("--voice")] = "alloy",
    response_format: Annotated[str, typer.Option("--response-format")] = "wav",
    purpose: Annotated[str | None, typer.Option("--purpose")] = None,
    target_latency_ms: Annotated[int | None, typer.Option("--target-latency-ms")] = None,
    license_policy: Annotated[str, typer.Option("--license-policy")] = "any",
    hardware_profile: Annotated[str | None, typer.Option("--hardware-profile")] = None,
    benchmark_dir: Annotated[Path | None, typer.Option("--benchmark-dir")] = Path("benchmarks/examples"),
    benchmark_suite: Annotated[str, typer.Option("--suite")] = "realtime-agent",
    default_model: Annotated[str, typer.Option("--default-model")] = "fake:tts",
    input_text: Annotated[str, typer.Option("--input")] = "Hello from TimbreGrid",
) -> None:
    try:
        request = SpeechRequest(
            model=model,
            input=input_text,
            voice=voice,
            response_format=response_format,
            purpose=purpose,
            target_latency_ms=target_latency_ms,
            license_policy=license_policy,
            hardware_profile=hardware_profile,
        )
        decision = resolve_route(
            request,
            default_model=default_model,
            benchmark_dir=benchmark_dir,
            suite=benchmark_suite,
        )
    except (ValueError, RouteNotFound) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    typer.echo(json.dumps(decision.to_dict(), indent=2, sort_keys=True))


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
    benchmark_dir: Annotated[Path | None, typer.Option("--benchmark-dir")] = None,
    voice_catalog: Annotated[Path | None, typer.Option("--voice-catalog")] = None,
) -> None:
    import uvicorn

    try:
        (
            resolved_model,
            resolved_host,
            resolved_port,
            resolved_benchmark_dir,
            resolved_voice_catalog,
        ) = resolve_serve_config(
            model,
            host,
            port,
            benchmark_dir,
            voice_catalog,
        )
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    try:
        app_instance = create_app(
            default_model=resolved_model,
            benchmark_dir=resolved_benchmark_dir,
            voice_catalog=resolved_voice_catalog,
        )
    except VoiceCatalogError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    uvicorn.run(
        app_instance,
        host=resolved_host,
        port=resolved_port,
    )


def resolve_serve_config(
    model: str | None = None,
    host: str | None = None,
    port: int | None = None,
    benchmark_dir: Path | None = None,
    voice_catalog: Path | None = None,
) -> tuple[str, str, int, Path | None, Path | None]:
    resolved_model = model or os.environ.get("TIMBREGRID_MODEL") or "fake:tts"
    resolved_host = host or os.environ.get("TIMBREGRID_HOST") or "127.0.0.1"
    resolved_port = port if port is not None else _env_port()
    resolved_benchmark_dir = benchmark_dir if benchmark_dir is not None else _env_benchmark_dir()
    resolved_voice_catalog = voice_catalog if voice_catalog is not None else _env_voice_catalog()
    return resolved_model, resolved_host, resolved_port, resolved_benchmark_dir, resolved_voice_catalog


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


def _env_benchmark_dir() -> Path | None:
    raw = os.environ.get("TIMBREGRID_BENCHMARK_DIR")
    if raw is None:
        return Path("benchmarks/examples")
    if raw == "":
        return None
    return Path(raw)


def _env_voice_catalog() -> Path | None:
    raw = os.environ.get("TIMBREGRID_VOICE_CATALOG")
    if raw is None or raw == "":
        return None
    return Path(raw)


app.add_typer(manifest_app, name="manifest")
app.add_typer(models_app, name="models")
app.add_typer(registry_app, name="registry")
app.add_typer(route_app, name="route")


if __name__ == "__main__":
    app()
