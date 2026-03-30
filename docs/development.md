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
make sync
```

Run the full test suite:

```bash
make test
```

Run linting:

```bash
make lint
```

Build artifacts locally:

```bash
make build
```

Run the suite against a specific Django series:

```bash
make test-django DJANGO_CONSTRAINT="django>=5.0,<5.1" PYTHON=3.12
```

If `uv` cannot write to the default cache directory in your environment, use:

```bash
UV_CACHE_DIR=.uv-cache make sync
UV_CACHE_DIR=.uv-cache make test
```

If you update dependencies, refresh the lockfile before syncing again:

```bash
make lock
make sync
```

## CI matrix

The GitHub Actions workflow validates the package against a compatibility matrix of Python and Django versions supported by Django upstream. Today that matrix covers:

- Python 3.11 with Django 4.2, 5.0, 5.1, and 5.2
- Python 3.12 with Django 4.2, 5.0, 5.1, and 5.2
- Python 3.13 with Django 5.1 and 5.2
- Python 3.14 with Django 5.2

## How to extend the command safely

When adding support for a new Django field or DBML feature:

1. Update the rendering logic in `django_dbml/management/commands/dbml.py`.
2. Add or adjust models inside `tests/testapp/models.py` to cover the new metadata shape.
3. Add assertions in `tests/test_command.py` for the rendered DBML.
4. If the change is isolated to a helper, add a focused unit test in `tests/test_utils.py`.

Prefer command-level tests for behavior that depends on Django model metadata, because the package's value is in the final DBML output rather than in isolated internal methods.
