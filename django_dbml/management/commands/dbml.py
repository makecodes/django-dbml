from django_dbml.utils import to_snake_case
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import models


class Command(BaseCommand):
    help = "Generate a DBML file based on Django models"

    def add_arguments(self, parser):
        parser.add_argument(
            'args', metavar='app_label[.ModelName]', nargs='*',
            help='Restricts dbml generation to the specified app_label or app_label.ModelName.',
        )

    def get_field_notes(self, field):
        if len(field.keys()) == 1:
            return ""

        attributes = []
        for name, value in field.items():
            if name == "type":
                continue

            if name == "note":
                attributes.append('note:"{}"'.format(value))
                continue

            if name in ("null", "pk", "unique"):
                attributes.append(name)
                continue

            attributes.append("{}:{}".format(name, value))
        if not attributes:
            return ""
        return "[{}]".format(", ".join(attributes))

    def get_app_tables(self, app_labels):
        # get the list of models to generate DBML for

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
                raise CommandError(str(e))

            app_config = apps.get_app_config(app_label)
            if model_label:
                app_tables.append(app_config.get_model(model_label))
            else:
                app_tables.extend(app_config.get_models())

        return app_tables

    def handle(self, *app_labels, **kwargs):
        all_fields = {}
        allowed_types = ["ForeignKey", "ManyToManyField"]
        for field_type in models.__all__:
            if "Field" not in field_type and field_type not in allowed_types:
                continue

            all_fields[field_type] = to_snake_case(field_type.replace("Field", ""),)

        ignore_types = (
            models.fields.reverse_related.ManyToOneRel,
            models.fields.reverse_related.ManyToManyRel,
        )

        tables = {}
        app_tables = self.get_app_tables(app_labels)

        for app_table in app_tables:
            table_name = app_table.__name__
            tables[table_name] = {"fields": {}, "relations": []}

            for field in app_table._meta.get_fields():
                if isinstance(field, ignore_types):
                    continue

                field_attributes = list(dir(field))

                # print(table_name, field, type(field))
                if isinstance(field, models.fields.related.OneToOneField):
                    tables[table_name]["relations"].append(
                        {
                            "type": "one_to_one",
                            "table_from": field.related_model.__name__,
                            "table_from_field": field.target_field.name,
                            "table_to": table_name,
                            "table_to_field": field.name,
                        }
                    )

                elif isinstance(field, models.fields.related.ForeignKey):
                    tables[table_name]["relations"].append(
                        {
                            "type": "one_to_many",
                            "table_from": field.related_model.__name__,
                            "table_from_field": field.target_field.name,
                            "table_to": table_name,
                            "table_to_field": field.name,
                        }
                    )

                elif isinstance(field, models.fields.related.ManyToManyField):
                    table_name_m2m = field.m2m_db_table()
                    # only define m2m table and relations on first encounter
                    if table_name_m2m not in tables.keys():
                        tables[table_name_m2m] = {"fields": {}, "relations": []}

                        tables[table_name_m2m]["relations"].append(
                            {
                                "type": "one_to_many",
                                "table_from": table_name_m2m,
                                "table_from_field": field.m2m_column_name(),
                                "table_to": field.model.__name__,
                                "table_to_field": field.m2m_target_field_name(),
                            }
                        )
                        tables[table_name_m2m]["relations"].append(
                            {
                                "type": "one_to_many",
                                "table_from": table_name_m2m,
                                "table_from_field": field.m2m_reverse_name(),
                                "table_to": field.related_model.__name__,
                                "table_to_field": field.m2m_target_field_name(),
                            }
                        )
                        tables[table_name_m2m]["fields"][field.m2m_reverse_name()] = {
                            "pk": True,
                            "type": "auto",
                        }

                        tables[table_name_m2m]["fields"][field.m2m_column_name()] = {
                            "pk": True,
                            "type": "auto",
                        }

                    continue

                tables[table_name]["fields"][field.name] = {
                    "type": all_fields.get(type(field).__name__),
                }

                if "help_text" in field_attributes:
                    help_text = field.help_text.replace('"', '\\"')
                    tables[table_name]["fields"][field.name]["note"] = help_text

                if "null" in field_attributes and field.null is True:
                    tables[table_name]["fields"][field.name]["null"] = True

                if "primary_key" in field_attributes and field.primary_key is True:
                    tables[table_name]["fields"][field.name]["pk"] = True

                if "unique" in field_attributes and field.unique is True:
                    tables[table_name]["fields"][field.name]["unique"] = True

                if app_table.__doc__:
                    tables[table_name]["note"] = app_table.__doc__

        for table_name, table in tables.items():
            print("Table {} {{".format(table_name))
            for field_name, field in table["fields"].items():
                print(
                    "  {} {} {}".format(
                        field_name, field["type"], self.get_field_notes(field)
                    )
                )
            if 'note' in table:
                print("  Note: '''{}'''".format(table['note']))
            print("}")

            for relation in table["relations"]:
                if relation["type"] == "one_to_many":
                    print(
                        "ref: {}.{} > {}.{}".format(
                            relation["table_to"],
                            relation["table_to_field"],
                            relation["table_from"],
                            relation["table_from_field"],
                        )
                    )

                if relation["type"] == "one_to_one":
                    print(
                        "ref: {}.{} - {}.{}".format(
                            relation["table_to"],
                            relation["table_to_field"],
                            relation["table_from"],
                            relation["table_from_field"],
                        )
                    )
            print("\n")
