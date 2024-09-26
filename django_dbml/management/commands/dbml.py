# ruff: noqa: SLF001
import hashlib
import inspect
import logging
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from textwrap import dedent

from django.apps import apps
from django.conf import settings
from django.contrib.postgres.indexes import HashIndex
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, models
from django.db.models import Model
from django.db.models.fields import Field

from django_dbml.utils import to_snake_case


logger = logging.getLogger('dbml')


class Command(BaseCommand):
    help = "Generate a DBML file based on Django models"

    def add_arguments(self, parser):  # noqa: D102
        # fmt: off
        parser.add_argument('args', metavar='app_label[.ModelName]', nargs='*', help='Restricts dbml generation to the specified app_label or app_label.ModelName.')
        parser.add_argument("--table_names", action="store_true", help='Use underlying table names rather than model names')
        parser.add_argument("--group_by_app", action="store_true")
        parser.add_argument("--color_by_app", action="store_true")
        parser.add_argument("--add_project_name", action="store", help="add name for the project")
        parser.add_argument("--add_project_notes", action="store", help="add notes to describe the project")
        parser.add_argument("--disable_update_timestamp", action="store_true", help="do not include a 'Last updated at' timestamp in the project notes.")
        parser.add_argument("--output_file", action="store", help="Put the generated schema in this file, rather than printing it to stdout.")
        # fmt: on

    def get_field_attributes(self, field: dict) -> str:  # noqa: PLR0912
        """Returns a string with the supported dbml attributes of a given field."""

        if len(field.keys()) == 1:
            return ""

        attributes = []
        for name, value in field.items():
            if name in {"type", "null"}:
                continue

            if name == "note":
                if value:
                    value_formatted = value.replace("'", '"')
                    if '\n' in value_formatted:
                        attributes.append(f"note: '''\n{value_formatted}'''")
                    else:
                        attributes.append(f"note: '''{value_formatted}'''")
                continue

            if name in {"pk", "unique"}:
                attributes.append(name)
                continue

            if name == "default":
                if callable(value):
                    value = f'{inspect.getmodule(value).__name__}.{value.__name__}()' if inspect.getmodule(value) else f'{value.__name__}()'  # noqa: PLW2901
                elif isinstance(value, str):
                    value = f'"{value}"'  # noqa: PLW2901
                attributes.append(f'default:`{value}`')
                continue

            attributes.append(f"{name}:{value}")

        if field.get('null'):
            attributes.append('null')
        else:
            attributes.append('not null')

        if not attributes:
            return ""
        return "[{}]".format(", ".join(attributes))

    def get_table_name(self, model: Model) -> str:
        """Return the name to use in dbml for the given model."""

        if self.options["table_names"]:
            return model._meta.db_table

        # Return the "<app_name>.<model_name>" format, to avoid clashes with the same model names being used in different apps.
        return model._meta.label

    def get_enum_choices(self, field: Field) -> list:
        """Returns the value and display_value for choices on a field."""

        return list(field.choices)

    def get_app_tables(self, app_labels) -> list:
        """Get the list of models to generate DBML for."""

        # if no apps are specified, process all models
        if not app_labels:
            return apps.get_models()

        # get specific models when app or app.model is specified
        app_tables = []
        for app in app_labels:
            app_label_parts = app.split('.')
            # first part is always the app label
            app_label = app_label_parts[0]
            # use the second part as model label if set
            model_label = app_label_parts[1] if len(app_label_parts) > 1 else None
            try:
                app_config = apps.get_app_config(app_label)
            except LookupError as e:
                raise CommandError(str(e))  # noqa: B904

            app_config = apps.get_app_config(app_label)
            if model_label:
                app_tables.append(app_config.get_model(model_label))
            else:
                app_tables.extend(app_config.get_models())

        return app_tables

    def get_tl_module_name(self, model: Model) -> str:
        """Get top level module of model."""

        parts = model.__module__.split(".")

        # Return the name of the app this model belongs to, if possible
        if len(parts) >= 2:  # noqa: PLR2004
            return parts[-2]

        return parts[0]

    def get_db_type(self) -> str:
        """Return which type of database is being used."""

        db = settings.DATABASES['default']

        if 'postgres' in db['ENGINE'].lower():
            return 'PostgreSQL'
        if 'sqlite' in db['ENGINE'].lower():
            return 'SQLite'
        if 'mysql' in db['ENGINE'].lower():
            return 'MySQL'
        if 'oracle' in db['ENGINE'].lower():
            return 'Oracle'
        if 'mssql' in db['ENGINE'].lower():
            return 'Microsoft SQL'

        return "Unknown ({})".format(db['ENGINE'])

    @cache  # noqa: B019
    def map_field_type_to_dbml_type(self, field: type[Field]) -> str:
        """Given a field class, return the type we should display it as in dbml."""
        return to_snake_case(field.__name__.removesuffix("Field"))

    def cleanup_docstring(self, input_docstring: str) -> str:
        """Returns a string with no leading whitespaces in the lines, so it is not weirdly rendered in dbdocs."""
        lines = input_docstring.split('\n')
        no_whitespaced_lines = [dedent(l) for l in lines]  # noqa: E741
        return '\n'.join(no_whitespaced_lines).strip('\n')

    def choices_to_markdown_table(self, choices: list) -> str:
        """Create a string containing a markdown-formatted table of a list of choices."""
        s = "| Value | Display |\n| -------- | ------- |"

        for choice in choices:
            s += f'\n|{choice[0]}|{choice[1]}|'

        return s

    def handle(self, *app_labels, **kwargs):  # noqa: D102, PLR0912, PLR0914, PLR0915
        self.options = kwargs
        project_name = self.options["add_project_name"]
        project_notes = self.options["add_project_notes"]

        ignore_types = (models.fields.reverse_related.ManyToOneRel, models.fields.reverse_related.ManyToManyRel)

        # Collect information on all models

        enums, tables, table_colors_and_groups = {}, {}, {}

        for app_table in self.get_app_tables(app_labels):
            tl_module_name = self.get_tl_module_name(app_table)

            table_color = "" if not self.options["color_by_app"] else f"#{hashlib.sha256(tl_module_name.encode()).hexdigest()[:6]}"

            table_name = self.get_table_name(app_table)
            tables[table_name] = {"fields": {}, "relations": [], 'indexes': [], 'note': ''}
            table_colors_and_groups[table_name] = {"color": table_color, "group": tl_module_name}

            for field in app_table._meta.get_fields():
                if isinstance(field, ignore_types):
                    continue

                field_name = field.name

                field_attributes = list(dir(field))

                # print(table_name, field, type(field))
                if isinstance(field, models.fields.related.OneToOneField):
                    field_name += '_id'  # the db column name always has this suffix added

                    tables[table_name]["relations"].append(
                        {
                            "type": "one_to_one",
                            "table_from": self.get_table_name(field.related_model),
                            "table_from_field": field.target_field.name,
                            "table_to": table_name,
                            "table_to_field": field_name,
                        }
                    )

                elif isinstance(field, models.fields.related.ForeignKey):
                    field_name += '_id'  # the db column name always has this suffix added

                    tables[table_name]["relations"].append(
                        {
                            "type": "one_to_many",
                            "table_from": self.get_table_name(field.related_model),
                            "table_from_field": field.target_field.name,
                            "table_to": table_name,
                            "table_to_field": field_name,
                        }
                    )

                elif isinstance(field, models.fields.related.ManyToManyField):
                    table_name_m2m: str = field.m2m_db_table()

                    # If there is no underscore in the through model, we assume it is explicitly specified by the user via the 'through' attribute on the M2M field.
                    # If it is specified, the through model will already have been included in the schema on its own when looping over the app_tables.
                    # So in that case, we do not want to have a separate, additional model here, since that model will never actually be used.
                    # (it would represent the autogenerated m2m intermediate model, but we are defining our own through model instead).
                    if '_' not in field.remote_field.through._meta.model_name:
                        continue

                    # If we reach here, we are dealing with a django-autogenerated m2m linking table.
                    # We should replace the name by a name which include the relevant app.
                    # If we don't do that, it would claim that this table is in a 'public' db schema, which is not true.
                    # It should belong with the app where the other models live.

                    old_table_name_m2m = table_name_m2m
                    if '_' in table_name_m2m:
                        table_name_m2m = table_name_m2m.replace('_', '.', 1)

                    # only define m2m table and relations on first encounter
                    if table_name_m2m not in tables:
                        tables[table_name_m2m] = {"fields": {}, "relations": [], 'indexes': [], 'note': ''}
                        # keep the color of the table for the m2m
                        table_colors_and_groups[table_name_m2m] = {"color": table_color, "group": tl_module_name}

                        tables[table_name_m2m]["relations"].append(
                            {
                                "type": "one_to_many",
                                "table_from": table_name_m2m,
                                "table_from_field": field.m2m_column_name(),
                                "table_to": self.get_table_name(field.model),
                                "table_to_field": field.m2m_target_field_name(),
                            }
                        )
                        tables[table_name_m2m]["relations"].append(
                            {
                                "type": "one_to_many",
                                "table_from": table_name_m2m,
                                "table_from_field": field.m2m_reverse_name(),
                                "table_to": self.get_table_name(field.related_model),
                                "table_to_field": field.m2m_reverse_target_field_name(),
                            }
                        )
                        tables[table_name_m2m]["fields"]['id'] = {"pk": True, "type": "auto"}
                        tables[table_name_m2m]["fields"][field.m2m_reverse_name()] = {"type": "auto"}
                        tables[table_name_m2m]["fields"][field.m2m_column_name()] = {"type": "auto"}

                        tables[table_name_m2m]['note'] = 'This is a Many-To-Many linking table autogenerated by Django.'
                        if not self.options["table_names"]:
                            tables[table_name_m2m]["note"] += f"\n\n*DB table: {old_table_name_m2m}*"

                        for f_name in [field.m2m_reverse_name(), field.m2m_column_name()]:
                            tables[table_name_m2m]['indexes'].append(
                                {
                                    'fields': [f_name],
                                    'type': 'btree',
                                    'name': connection.schema_editor()._create_index_name(old_table_name_m2m, [f_name]),
                                    'unique': False,
                                    'pk': False,
                                }
                            )
                        tables[table_name_m2m]['indexes'].append(
                            {'fields': ['id'], 'type': 'btree', 'name': f'{old_table_name_m2m}_pkey', 'unique': True, 'pk': True}
                        )
                        tables[table_name_m2m]["indexes"].append(
                            {
                                'fields': [field.m2m_column_name(), field.m2m_reverse_name()],
                                'type': 'btree',
                                'name': connection.schema_editor()._unique_constraint_name(
                                    old_table_name_m2m, [field.m2m_column_name(), field.m2m_reverse_name()], quote=False
                                ),
                                'unique': True,
                                'pk': False,
                            }
                        )

                    continue

                tables[table_name]["fields"][field_name] = {"type": self.map_field_type_to_dbml_type(type(field)), 'note': ''}

                if "db_comment" in field_attributes and field.db_comment:
                    tables[table_name]["fields"][field_name]["note"] += field.db_comment.replace('"', '\\"')

                if "help_text" in field_attributes and field.help_text:
                    help_text = field.help_text.replace('"', '\\"')
                    tables[table_name]["fields"][field_name]["note"] += f"\n{help_text}"

                if "null" in field_attributes and field.null is True:
                    tables[table_name]["fields"][field_name]["null"] = True

                if "primary_key" in field_attributes and field.primary_key is True:
                    tables[table_name]["fields"][field_name]["pk"] = True

                if "db_index" in field_attributes and (field.db_index or field.primary_key or field.unique):
                    if field.primary_key:
                        index_name = f'{app_table._meta.db_table}_pkey'
                    elif isinstance(field, models.fields.related.OneToOneField) or field.unique:
                        index_name = f'{app_table._meta.db_table}_{field_name}_key'
                    else:
                        index_name = connection.schema_editor()._create_index_name(app_table._meta.db_table, [field_name])

                    tables[table_name]['indexes'].append(
                        {'fields': [field_name], 'type': 'btree', 'name': index_name, 'unique': field.unique, 'pk': field.primary_key}
                    )

                if "unique" in field_attributes and field.unique is True:
                    tables[table_name]["fields"][field_name]["unique"] = True

                if "default" in field_attributes and field.default != models.fields.NOT_PROVIDED:
                    tables[table_name]["fields"][field_name]["default"] = field.default

                if 'choices' in field_attributes and field.choices:
                    if '.' in table_name:
                        schema_name, model_name = table_name.split('.')
                    elif '_' in table_name:
                        schema_name, model_name = table_name.split('_')

                    enum_name = f'{schema_name}.{tables[table_name]["fields"][field_name]["type"]}_{model_name}_{field_name}'.lower()

                    tables[table_name]["fields"][field_name]['type'] = enum_name
                    enums[enum_name] = '\n  '.join([f"\"{c[0]}\" [note: '''{c[1]}''']" for c in self.get_enum_choices(field)])

                if 'base_field' in field_attributes and field.base_field.choices:
                    tables[table_name]["fields"][field_name]["note"] += f'\n\nBase field choices ({self.map_field_type_to_dbml_type(type(field.base_field))}):'
                    tables[table_name]["fields"][field_name]["note"] += f'\n{self.choices_to_markdown_table(field.base_field.choices)}'

                tables[table_name]["fields"][field_name]["note"] = tables[table_name]["fields"][field_name]["note"].strip('\n')

            # Indexes declared on individual fields have been added while looping over the fields above.
            # Here, add indices from class Meta: indexes and unique_together
            if app_table._meta.indexes:
                for index in app_table._meta.indexes:
                    column_names_in_index = [app_table._meta._forward_fields_map[field].column for field in index.fields]

                    tables[table_name]["indexes"].append(
                        {
                            'fields': column_names_in_index,
                            'type': 'btree' if not isinstance(index, HashIndex) else 'hash',
                            'name': index.name,
                            'unique': False,
                            'pk': False,
                        }
                    )
            if app_table._meta.unique_together:
                for unique_together in app_table._meta.unique_together:
                    column_names_in_index = [app_table._meta._forward_fields_map[field].column for field in unique_together]

                    tables[table_name]["indexes"].append(
                        {
                            'fields': column_names_in_index,
                            'type': 'btree',
                            'name': connection.schema_editor()._unique_constraint_name(app_table._meta.db_table, column_names_in_index, quote=False),
                            'unique': True,
                            'pk': False,
                        }
                    )

            if app_table.__doc__:
                tables[table_name]["note"] += f"\n{app_table.__doc__}"

            if app_table._meta.db_table_comment:
                comment = app_table._meta.db_table_comment.replace('"', '\"')
                tables[table_name]["note"] += f'\n\n*DB comment: {comment}*'

            if not self.options["table_names"]:
                tables[table_name]["note"] += f"\n\n*DB table: {app_table._meta.db_table}*"

        # Generate output string from the collected info
        output_blocks = []

        if not self.options.get('disable_update_timestamp'):
            ts = datetime.now(UTC).strftime('%m-%d-%Y %I:%M%p UTC')
            output_blocks += [
                f'Project "{project_name}" {{\n  database_type: \'{self.get_db_type()}\'\n  Note: \'\'\'{project_notes}\n  Last Updated At {ts}\'\'\'\n}}\n'
            ]
        else:
            output_blocks += [f'Project "{project_name}" {{\n  database_type: \'{self.get_db_type()}\'\n  Note: \'\'\'{project_notes}\'\'\'\n}}\n']

        for enum_name, enum in sorted(enums.items()):
            output_blocks += [f"enum {enum_name} {{\n  {enum}\n}}\n"]

        for table_name, table in sorted(tables.items()):
            if self.options["color_by_app"]:
                output_blocks += ["Table {} [headercolor: {}] {{".format(table_name, table_colors_and_groups[table_name]["color"])]
            else:
                output_blocks += [f"Table {table_name} {{"]

            if table.get('note'):
                output_blocks += ["  Note: '''\n{}'''\n".format(self.cleanup_docstring(table['note']))]

            for field_name, field in table["fields"].items():
                output_blocks += ["  {} {} {}".format(field_name, field["type"], self.get_field_attributes(field)).rstrip()]
            if table.get('indexes'):
                output_blocks += ['\n  indexes {']
                for index in sorted(table['indexes'], key=lambda x: str(x['name'])):
                    fields_as_list = '({})'.format(','.join(index['fields']))
                    index_attributes = []
                    if index['pk']:
                        index_attributes.append('pk')
                    if index['unique']:
                        index_attributes.append('unique')

                    index_attributes.append(f"name: '{index['name']}'")  # noqa: FURB113
                    index_attributes.append(f"type: {index['type']}")

                    index_string = f"{fields_as_list} [{', '.join(index_attributes)}]"
                    output_blocks += [f'    {index_string}']
                output_blocks += ['  }']
            output_blocks += ["}"]

            for relation in table["relations"]:
                if relation["type"] == "one_to_many":
                    output_blocks += [
                        "ref: {}.{} > {}.{}".format(relation["table_to"], relation["table_to_field"], relation["table_from"], relation["table_from_field"])
                    ]

                if relation["type"] == "one_to_one":
                    output_blocks += [
                        "ref: {}.{} - {}.{}".format(relation["table_to"], relation["table_to_field"], relation["table_from"], relation["table_from_field"])
                    ]
            output_blocks += ['\n']

        if self.options["group_by_app"]:
            groups = {}
            for table_name, group_color_dict in sorted(table_colors_and_groups.items()):
                group = group_color_dict["group"]
                if group in groups:
                    groups[group].append(table_name)
                else:
                    groups[group] = [table_name]

            for group, tables in sorted(groups.items()):
                output_blocks += [f"TableGroup {group} {{"]
                for table in tables:
                    output_blocks += [f"  {table}"]
                output_blocks += ["}\n"]

        output_string = '\n'.join(output_blocks)

        # Output the result either to a file, or to stdout

        output_file = self.options.get('output_file')
        if output_file:
            with Path(output_file).open('w', encoding="utf-8") as f:
                f.write(output_string)
            logger.info('Generated dbml file to %s', output_file)
        else:
            print(output_string)  # noqa: T201
