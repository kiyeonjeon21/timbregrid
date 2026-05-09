# Security Policy

## Reporting Security Issues

Please open a private security advisory on GitHub if available. If private advisories are not available, open an issue with minimal public detail and ask for a private contact path.

Do not include secrets, private voice samples, private datasets, API keys, consent records, or sensitive logs in public issues.

## Scope

Security-sensitive areas include:

- gateway request handling;
- path or URL handling for future voice references;
- benchmark and manifest parsing;
- dependency loading for optional model adapters;
- voice provenance and consent enforcement once implemented.

## Voice Safety

TimbreGrid should not host public cloned voice samples by default. Any future cloning workflow must keep provenance and consent metadata explicit and local-first unless a user intentionally configures otherwise.

## Supported Versions

The project is pre-1.0. Security fixes target the `main` branch until release branches exist.
