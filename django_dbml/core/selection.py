from django.apps import apps
from django.core.management.base import CommandError
from django.db import models
from django.db.models import Model


IGNORE_RELATION_TYPES = (
    models.fields.reverse_related.ManyToManyRel,
    models.fields.reverse_related.ManyToOneRel,
)


def select_models(app_labels: tuple[str, ...]) -> list[type[Model]]:
    """Return the models that should participate in generation."""

    if not app_labels:
        return list(apps.get_models())

    selected_models: list[type[Model]] = []
    for app_label_spec in app_labels:
        app_label, _, model_label = app_label_spec.partition(".")

        try:
            app_config = apps.get_app_config(app_label)
        except LookupError as exc:
            raise CommandError(str(exc)) from exc

        if model_label:
            selected_models.append(app_config.get_model(model_label))
            continue

        selected_models.extend(app_config.get_models())

    return include_related_models(selected_models)


def include_related_models(models_to_process: list[type[Model]]) -> list[type[Model]]:
    """Expand a selected set of models to include their forward-related models."""

    collected_models: list[type[Model]] = []
    pending_models = list(models_to_process)
    seen_models: set[type[Model]] = set()

    while pending_models:
        model = pending_models.pop(0)
        if model in seen_models:
            continue

        seen_models.add(model)
        collected_models.append(model)

        for field in model._meta.get_fields():
            if isinstance(field, IGNORE_RELATION_TYPES):
                continue

            if isinstance(field, (models.fields.related.ForeignKey, models.fields.related.OneToOneField)):
                pending_models.append(field.related_model)
                continue

            if isinstance(field, models.fields.related.ManyToManyField):
                pending_models.append(field.related_model)

                through_model = field.remote_field.through
                if through_model is not None and not through_model._meta.auto_created:
                    pending_models.append(through_model)

    return collected_models


def get_model_group(model: type[Model]) -> str:
    """Return a stable group name for a model."""

    module_parts = model.__module__.split(".")
    if len(module_parts) >= 2:  # noqa: PLR2004
        return module_parts[-2]

    return module_parts[0]
