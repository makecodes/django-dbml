SHELL := /bin/sh

UV ?= uv
UV_CACHE_DIR ?= .uv-cache
PYTHON ?=
DJANGO_CONSTRAINT ?=

UV_ENV = UV_CACHE_DIR=$(UV_CACHE_DIR)

.PHONY: help sync lock test test-django lint build check ci

help:
	@printf '%s\n' \
		'make sync        - sync the development environment from uv.lock' \
		'make lock        - refresh uv.lock after dependency changes' \
		'make test        - run the unit test suite with the locked environment' \
		'make test-django - run tests against a specific Django constraint' \
		'                   example: make test-django DJANGO_CONSTRAINT="django>=5.1,<5.2" PYTHON=3.13' \
		'make lint        - run Ruff checks' \
		'make build       - build wheel and sdist artifacts' \
		'make check       - run lint and tests' \
		'make ci          - run lint, tests, and build locally'

sync:
	$(UV_ENV) $(UV) sync --locked

lock:
	$(UV_ENV) $(UV) lock

test:
	$(UV_ENV) $(UV) run --locked pytest

test-django:
	@if [ -z "$(DJANGO_CONSTRAINT)" ]; then \
		printf '%s\n' 'DJANGO_CONSTRAINT is required. Example: make test-django DJANGO_CONSTRAINT="django>=5.1,<5.2" [PYTHON=3.13]'; \
		exit 2; \
	fi
	$(UV_ENV) $(UV) run --locked --isolated $(if $(PYTHON),--python $(PYTHON),) --with "$(DJANGO_CONSTRAINT)" pytest

lint:
	$(UV_ENV) $(UV) run --locked ruff check .

build:
	$(UV_ENV) $(UV) build

check: sync lint test

ci: sync lint test build
