# Django DBML generator

This app can generate a DBML output for all installed models.

## Installation

```bash
pip install django-dbml
```

## Usage

Add `django_dbml` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_dbml",
]
```

Generate DBML from all installed models:

```bash
python manage.py dbml
```

To generate DBML for a subset of your models, specify one or more Django app
names or models by `app_label` or `app_label.ModelName`. Related tables will still
be included in the DBML.

## Development

This repository is now managed with `uv`.

```bash
make sync
make test
make lint
make build
```

Development instructions live in [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/development.md](docs/development.md).

# Thanks

The initial code was based on https://github.com/hamedsj/DbmlForDjango project
