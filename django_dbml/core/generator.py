from django_dbml.core.builder import SchemaBuilder
from django_dbml.core.options import GenerationOptions
from django_dbml.core.renderer import DbmlRenderer


def generate_dbml(app_labels: tuple[str, ...], options: GenerationOptions) -> str:
    project = SchemaBuilder(options).build(app_labels)
    return DbmlRenderer(options).render(project)
