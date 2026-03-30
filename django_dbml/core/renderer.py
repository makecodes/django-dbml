import inspect
from datetime import UTC, datetime

from django_dbml.core.options import GenerationOptions
from django_dbml.core.schema import FieldDefinition, ProjectDefinition, RelationDefinition, TableDefinition
from django_dbml.utils import cleanup_docstring


class DbmlRenderer:
    def __init__(self, options: GenerationOptions) -> None:
        self.options = options

    def render(self, project: ProjectDefinition) -> str:
        output_blocks = [self.render_project_block(project)]
        output_blocks.extend(self.render_enums(project))
        output_blocks.extend(self.render_tables(project))

        if self.options.group_by_app:
            output_blocks.extend(self.render_groups(project))

        return "\n".join(output_blocks)

    def render_project_block(self, project: ProjectDefinition) -> str:
        project_notes = project.notes
        if project.include_timestamp:
            timestamp = datetime.now(UTC).strftime("%m-%d-%Y %I:%M%p UTC")
            project_notes = f"{project_notes}\n  Last Updated At {timestamp}"

        return (
            f'Project "{project.name}" {{\n'
            f"  database_type: '{project.database_type}'\n"
            f"  Note: '''{project_notes}'''\n"
            "}\n"
        )

    def render_enums(self, project: ProjectDefinition) -> list[str]:
        blocks = []
        for enum_name, values in sorted(project.enums.items()):
            rendered_values = "\n  ".join([f"\"{value.value}\" [note: '''{value.display}''']" for value in values])
            blocks.append(f"enum {enum_name} {{\n  {rendered_values}\n}}\n")
        return blocks

    def render_tables(self, project: ProjectDefinition) -> list[str]:
        blocks: list[str] = []

        for table_name, table in sorted(project.tables.items()):
            blocks.extend(self.render_table(table_name, table))

        return blocks

    def render_table(self, table_name: str, table: TableDefinition) -> list[str]:
        blocks = []
        if self.options.color_by_app:
            blocks.append(f"Table {table_name} [headercolor: {table.color}] {{")
        else:
            blocks.append(f"Table {table_name} {{")

        if table.note:
            blocks.append("  Note: '''\n{}'''\n".format(cleanup_docstring(table.note)))

        for field_name, field in table.fields.items():
            blocks.append(f"  {field_name} {field.type} {self.render_field_attributes(field)}".rstrip())

        if table.indexes:
            blocks.append("\n  indexes {")
            for index in sorted(table.indexes, key=lambda item: str(item.name)):
                blocks.append(f"    {self.render_index(index.fields, index.pk, index.unique, index.name, index.type)}")
            blocks.append("  }")

        blocks.append("}")
        for relation in table.relations:
            blocks.append(self.render_relation(relation))
        blocks.append("\n")
        return blocks

    def render_field_attributes(self, field: FieldDefinition) -> str:  # noqa: PLR0912
        attributes = []

        if field.note:
            note = field.note.replace("'", '"')
            if "\n" in note:
                attributes.append(f"note: '''\n{note}'''")
            else:
                attributes.append(f"note: '''{note}'''")

        if field.pk:
            attributes.append("pk")

        if field.unique:
            attributes.append("unique")

        if field.has_default:
            attributes.append(f"default:`{self.format_default(field.default)}`")

        attributes.append("null" if field.null else "not null")
        return f"[{', '.join(attributes)}]" if attributes else ""

    def format_default(self, value: object) -> object:
        if callable(value):
            if module := inspect.getmodule(value):
                return f"{module.__name__}.{value.__name__}()"
            return f"{value.__name__}()"

        if isinstance(value, str):
            return f'"{value}"'

        return value

    def render_index(self, fields: list[str], pk: bool, unique: bool, name: str, index_type: str) -> str:
        index_attributes = []
        if pk:
            index_attributes.append("pk")
        if unique:
            index_attributes.append("unique")

        index_attributes.append(f"name: '{name}'")
        index_attributes.append(f"type: {index_type}")
        return f"({','.join(fields)}) [{', '.join(index_attributes)}]"

    def render_relation(self, relation: RelationDefinition) -> str:
        operator = ">" if relation.kind == "one_to_many" else "-"
        return f"ref: {relation.table_to}.{relation.table_to_field} {operator} {relation.table_from}.{relation.table_from_field}"

    def render_groups(self, project: ProjectDefinition) -> list[str]:
        grouped_tables: dict[str, list[str]] = {}
        for table_name, table in sorted(project.tables.items()):
            grouped_tables.setdefault(table.group, []).append(table_name)

        blocks = []
        for group_name, table_names in sorted(grouped_tables.items()):
            blocks.append(f"TableGroup {group_name} {{")
            for table_name in table_names:
                blocks.append(f"  {table_name}")
            blocks.append("}\n")

        return blocks
