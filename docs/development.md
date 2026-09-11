# Development Guide

## What this extension does

`django-dbml` is a Django app that converts the metadata exposed by Django models into DBML. The main entrypoint is the `dbml` management command.

## How the generator is organized

The command entrypoint in `django_dbml/management/commands/dbml.py` is intentionally thin. The core is split like this:

1. `django_dbml/core/options.py`: normalized generation options.
2. `django_dbml/core/selection.py`: model selection and inclusion of forward-related models.
3. `django_dbml/core/builder.py`: conversion from Django model metadata to an intermediate schema.
4. `django_dbml/core/schema.py`: dataclasses representing the intermediate schema.
5. `django_dbml/core/renderer.py`: conversion from the intermediate schema to DBML text.
6. `django_dbml/core/generator.py`: orchestration layer used by the command.

`django_dbml/utils.py` contains small reusable string-formatting helpers.

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

The GitHub Actions workflow validates the package against every combination it
claims to support: each Python in `project.classifiers` crossed with each Django
series allowed by the `django` specifier in `project.dependencies`, minus the
pairs upstream Django does not support. That is 17 legs today:

| Python | Django series |
| ------ | ------------- |
| 3.11   | 4.2, 5.0, 5.1, 5.2 |
| 3.12   | 4.2, 5.0, 5.1, 5.2, 6.0, 6.1 |
| 3.13   | 5.1, 5.2, 6.0, 6.1 |
| 3.14   | 5.2, 6.0, 6.1 |

The gaps are upstream constraints, not omissions: Django 4.2 and 5.0 do not
support Python 3.13, and Django 6.x requires Python 3.12 or newer.

**Widening `requires-python` or the `django` specifier in `pyproject.toml`
without widening this matrix ships an untested claim of support.** Add the legs
in the same pull request, and keep the `Framework :: Django ::` classifiers in
step.

Each leg prints the Django and Python versions it actually resolved to the job
summary, so a constraint that silently fails to take effect is visible instead
of passing as a false green.

CI runs on every pull request and on pushes to `main`. Superseded runs for the
same pull request are cancelled automatically. `Required Checks` aggregates the
whole workflow into one stable check name, which is what branch protection
should require: the matrix job names change whenever a series is added or
dropped.

## How to extend the command safely

When adding support for a new Django field or DBML feature:

1. If the change affects model discovery, update `django_dbml/core/selection.py`.
2. If the change affects schema extraction from Django models, update `django_dbml/core/builder.py`.
3. If the change affects DBML text output, update `django_dbml/core/renderer.py`.
4. Add or adjust models inside `tests/testapp/models.py` to cover the new metadata shape.
5. Add assertions in `tests/test_command.py` for the rendered DBML.
6. If the change is isolated to a helper, add a focused unit test in `tests/test_utils.py`.

Prefer command-level tests for behavior that depends on Django model metadata, because the package's value is in the final DBML output rather than in isolated internal methods.
