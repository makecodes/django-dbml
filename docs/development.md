# Development Guide

## What this extension does

`django-dbml` is a Django app that converts the metadata exposed by Django models into DBML. The main entrypoint is the `dbml` management command.

## How the generator is organized

`django_dbml/management/commands/dbml.py` is responsible for:

1. Selecting which models should be part of the schema.
2. Expanding the selection to include forward-related models.
3. Mapping Django field classes to DBML field types.
4. Rendering tables, enums, indexes, notes, and references.

`django_dbml/utils.py` contains the field-name normalization helper used during type mapping.

## Local development workflow

Install dependencies:

```bash
uv sync --locked
```

Run the full test suite:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check .
```

Build artifacts locally:

```bash
uv build
```

If `uv` cannot write to the default cache directory in your environment, use:

```bash
UV_CACHE_DIR=.uv-cache uv sync --locked
UV_CACHE_DIR=.uv-cache uv run pytest
```

If you update dependencies, refresh the lockfile before syncing again:

```bash
uv lock
uv sync
```

## How to extend the command safely

When adding support for a new Django field or DBML feature:

1. Update the rendering logic in `django_dbml/management/commands/dbml.py`.
2. Add or adjust models inside `tests/testapp/models.py` to cover the new metadata shape.
3. Add assertions in `tests/test_command.py` for the rendered DBML.
4. If the change is isolated to a helper, add a focused unit test in `tests/test_utils.py`.

Prefer command-level tests for behavior that depends on Django model metadata, because the package's value is in the final DBML output rather than in isolated internal methods.
