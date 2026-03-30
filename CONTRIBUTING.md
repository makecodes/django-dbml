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

- `django_dbml/management/commands/dbml.py`: command that inspects Django model metadata and renders DBML
- `django_dbml/utils.py`: helper utilities used by the generator
- `tests/testapp/`: isolated Django app used to exercise the extension
- `tests/test_command.py`: command-level tests
- `tests/test_utils.py`: unit tests for helper behavior

## Release flow

The repository publishes from GitHub Actions using `uv build` and `uv publish`. Before releasing, run:

```bash
make test
make lint
make build
```

The detailed development guide lives in `docs/development.md`.
