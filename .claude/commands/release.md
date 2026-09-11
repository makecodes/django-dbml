---
description: Prepare a django-dbml release. Bump the version, verify locally, and hand over the tag command.
argument-hint: "[new version, e.g. 1.2.0]"
---

Prepare the release for version `$1` (ask for it if empty).

Publishing is tag-driven and gated: `.github/workflows/production.yml` reads `project.version` from `pyproject.toml`, **fails if the pushed tag does not match it exactly**, reuses `ci.yml` as a gate, builds the artifacts once, and publishes those exact artifacts to PyPI via Trusted Publishing from the `pypi` environment.

Do this:

1. Confirm the working tree is clean and on `main`, up to date with `origin/main`.
2. Check `git tag -l "$1"` and the PyPI release history. Refuse if the version already exists.
3. Bump `project.version` in `pyproject.toml` to `$1`. Bump nothing else; there is no `__version__` in the package.
4. Run `make ci` and report the real output. Stop on any failure.
5. Review `git log <previous tag>..HEAD --oneline` and summarize the user-visible changes.
6. Commit as `chore: bump version to $1` and open a PR. **Do not tag from an unmerged branch.**

Then stop and tell the user the tag has to be pushed only after the version bump is merged to `main`:

```bash
git checkout main && git pull
git tag $1
git push origin $1
```

The tag carries **no `v` prefix**: the workflow trigger is `*.*.*` and the tag must equal `project.version` verbatim.

Never run `uv publish` or `twine upload` locally: the only supported publishing path is the GitHub Actions Trusted Publishing flow.
