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
- `tests/dbml_parser.py`: reads generated DBML back so tests can assert on its structure
- `tests/test_command.py`: command-level tests, including every documented CLI option
- `tests/test_builder.py`: unit tests for model introspection that is awkward to reach through the command
- `tests/test_renderer.py`: unit tests for DBML formatting details
- `tests/test_utils.py`: unit tests for helper behavior
- `CLAUDE.md`: architecture notes and repository conventions, read automatically by Claude Code
- `.claude/`: shared Claude Code configuration (command permissions and project slash commands)

`CLAUDE.md` and `.claude/` are committed so that AI-assisted contributions follow the same
pipeline boundaries, testing style, and release process as everything else. They are optional
tooling: nothing in the build, test, or release flow depends on them. Per-developer overrides
belong in `.claude/settings.local.json`, which is gitignored.

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
- the `pypi` environment requires a manual approval before the publish job runs
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
# after bumping project.version in pyproject.toml
make lock
make test
make lint
make build
git tag X.Y.Z
git push origin X.Y.Z
```

Replace `X.Y.Z` with the value of `project.version` in `pyproject.toml`. The tag must match it
exactly, with no `v` prefix, or the release workflow fails before publishing anything.

`make lock` is part of the bump, not an afterthought. The package is a member of its own
workspace, so `uv.lock` records `project.version`, and a lockfile that disagrees with
`pyproject.toml` fails every `uv sync --locked`, starting with the release workflow's own sync
step.

After the tag is pushed, the PyPI workflow publishes that version if CI passes, the tag matches
the package version, and someone approves the `pypi` environment deployment. Until that approval
the run sits at `waiting`, with every check green and nothing published.

If you use GitHub Releases, create the release from the existing version tag instead of using branch pushes as the release trigger.

The detailed development guide lives in `docs/development.md`.
