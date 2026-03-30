# Security Policy

## Supported Release Process

This project follows a tag-driven release process for production publishing:

- CI runs on pull requests and pushes
- production publishing runs only from tags matching `vX.Y.Z`
- the release workflow validates that the Git tag matches `project.version`
- production and TestPyPI publishing use Trusted Publishing with GitHub OIDC
- release artifacts are built in CI and published from those exact artifacts

## Reporting a Vulnerability

Please do not open a public issue for suspected security vulnerabilities.

Instead:

1. Contact the maintainers privately.
2. Include a clear description of the issue, affected versions, impact, and reproduction steps.
3. If possible, include a proposed fix or mitigation.

Until a dedicated private reporting channel is published for this repository, use the maintainer contact listed in `pyproject.toml`.

## Supply Chain Controls

This repository uses several controls intended to reduce supply-chain risk:

- third-party GitHub Actions are pinned to immutable commit SHAs
- pull requests run dependency review checks
- publishing is gated by CI and uses Trusted Publishing
- GitHub Actions dependency updates are handled through Dependabot

These controls reduce risk, but they do not eliminate it. Review dependency changes and release workflow changes carefully.
