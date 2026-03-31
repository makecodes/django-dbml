# Contributing

## Prerequisites

- `uv` installed locally
- Python `3.13` available, as declared in `.python-version`

## Bootstrap

```bash
make sync
```

If your environment cannot write to the default uv cache location, prefix the commands with `UV_CACHE_DIR=.uv-cache`.

If you change dependencies in `pyproject.toml`, regenerate the lockfile with:

```bash
make lock
make sync
```

## Daily commands

Run the unit tests:

```bash
make test
```

Run lint checks:

```bash
make lint
```

Build the package:

```bash
make build
```

Test against a specific Django branch:

```bash
make test-django DJANGO_CONSTRAINT="django>=5.1,<5.2" PYTHON=3.13
```

## Project layout

- `django_dbml/management/commands/dbml.py`: thin Django management command entrypoint
- `django_dbml/core/options.py`: generation options shared across the core
- `django_dbml/core/selection.py`: model selection and related-model expansion
- `django_dbml/core/builder.py`: Django model introspection and schema assembly
- `django_dbml/core/renderer.py`: DBML rendering
- `django_dbml/core/schema.py`: intermediate dataclasses for tables, fields, indexes, enums, and relations
- `django_dbml/utils.py`: small string-formatting helpers
- `tests/testapp/`: isolated Django app used to exercise the extension
- `tests/test_command.py`: command-level tests
- `tests/test_utils.py`: unit tests for helper behavior

## Release flow

The repository publishes from GitHub Actions using a gated release flow:

- `CI` runs the Django/Python compatibility matrix
- `CI` runs lint separately
- `CI` runs a package build check separately
- publish workflows reuse `CI` before building release artifacts
- release artifacts are built once, uploaded, and published from those exact artifacts
- production publishing happens only from tags in the format `X.Y.Z`
- the production workflow validates that the Git tag matches `project.version`
- publishing uses PyPI Trusted Publishing, not long-lived API tokens
- TestPyPI publishing is manual via `workflow_dispatch`
- TestPyPI can also use Trusted Publishing when configured on TestPyPI

Before releasing locally, run:

```bash
make test
make lint
make build
```

Recommended production release flow:

```bash
make test
make lint
make build
git tag 1.1.2
git push origin 1.1.2
```

After the tag is pushed, the PyPI workflow publishes that version if CI passes and the tag matches the package version.

If you use GitHub Releases, create the release from the existing version tag instead of using branch pushes as the release trigger.

The detailed development guide lives in `docs/development.md`.
