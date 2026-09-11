---
description: Add support for a new Django field type or DBML feature, following this repo's pipeline boundaries.
argument-hint: "[what to support, e.g. GeneratedField or DBML composite refs]"
---

Add generator support for: `$ARGUMENTS`

Respect the one-way pipeline. Decide first which single stage owns the change, then work outward:

- does it change **which models are emitted**? → `django_dbml/core/selection.py`
- does it change **what is read from Django**? → `django_dbml/core/builder.py`
- does it change **the emitted text**? → `django_dbml/core/renderer.py`
- does it need a **new attribute to carry across**? → add it to the dataclasses in `django_dbml/core/schema.py`

The renderer must not import Django model APIs, and the builder must not format DBML. `core/schema.py` is the contract between them.

Before writing code, check whether the change is even needed: `map_field_type_to_dbml_type` derives the DBML type from the field class name (`to_snake_case(ClassName.removesuffix("Field"))`), so most new Django field types already work. If only the name comes out wrong, fix `django_dbml/utils.to_snake_case` instead of adding a mapping.

Watch the invariants documented in `CLAUDE.md`:

- FK/O2O columns are `{field.name}_id`, and every `ref` endpoint must point at a column the table actually declares, or dbdiagram rejects the entire schema.
- `RelationDefinition.table_to` renders on the **left** side of the emitted `ref`.
- Table names are dual (`model._meta.label` vs `db_table`, via `--table_names`) and feed relation endpoints and enum names too.

Then:

1. Add the metadata shape to `tests/testapp/models.py`. That app is the fixture for every generator behavior.
2. Assert on the **rendered DBML** in `tests/test_command.py`. Use `disable_update_timestamp=True` so the output is reproducible. Only add to `tests/test_utils.py` if the change is a pure helper.
3. Run `make check`.
4. When the change touches `_meta` or `schema_editor` internals, also run both ends of the supported range locally before pushing, because those are the legs most likely to diverge:

   ```bash
   make test-django DJANGO_CONSTRAINT="django>=4.2,<4.3" PYTHON=3.11
   make test-django DJANGO_CONSTRAINT="django>=6.1,<6.2" PYTHON=3.14
   ```
5. Update `README.md` if the behavior is user-facing, and `docs/development.md` if it moves a pipeline boundary.
