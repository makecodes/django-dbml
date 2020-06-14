from django_dbml.utils import to_snake_case
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models


class Command(BaseCommand):
    help = "The main DBML management file"

    def get_field_notes(self, field):
        if len(field.keys()) == 1:
            return ""

        attributes = []
        for name, value in field.items():
            if name == "type":
                continue

            if name == "note":
                attributes.append("note:\"{}\"".format(value))
                continue

            if name in ("null", "pk", "unique"):
                attributes.append(name)
                continue

            attributes.append("{}:{}".format(name, value))
        if not attributes:
            return ""
        return "[{}]".format(", ".join(attributes))

    def handle(self, *args, **kwargs):
        all_fields = {}
        for field_type in models.__all__:
            if "Field" not in field_type:
                continue
            all_fields[field_type] = to_snake_case(field_type.replace("Field", ""))
        fields_available = all_fields.keys()

        tables = {}
        relations = []
        relation_types = (models.ManyToManyField, models.OneToOneField, models.ForeignKey)
        app_tables = apps.get_models()
        for app_table in app_tables:
            keys = app_table.__dict__.keys()
            table_name = app_table.__name__
            tables[table_name] = {
                "fields": {},
            }
            for key in keys:
                value = app_table.__dict__[key]

                # Check the fields and ManyToMany relations only
                if not isinstance(
                    value,
                    (
                        models.fields.related_descriptors.ManyToManyDescriptor,
                        models.query_utils.DeferredAttribute,
                    ),
                ):
                    continue

                field = value.__dict__["field"]
                if (
                    isinstance(field, models.ManyToManyField)
                    and field.related_model == app_table
                ):
                    continue

                field_type_name = all_fields.get(type(field).__name__)
                if not field_type_name:
                    continue

                tables[table_name]["fields"][field.name] = {
                    "type": field_type_name,
                }

                if field.help_text:
                    tables[table_name]["fields"][field.name]["note"] = field.help_text

                if field.null is True:
                    tables[table_name]["fields"][field.name]["null"] = True

                if field.primary_key is True:
                    tables[table_name]["fields"][field.name]["pk"] = True

                if field.unique is True:
                    tables[table_name]["fields"][field.name]["unique"] = True

                if not field.default == models.fields.NOT_PROVIDED:
                    tables[table_name]["fields"][field.name]["default"] = field.default

                # if isinstance(field, models.ManyToManyField):
                #     if field.to_fields and field.to_fields[0] is not None and field.to_fields[0] != 'self':
                #         print("ref: "+app_table.__name__+"."+field.name+" > "+str(field.related_model.__name__)+"."+field.to_fields[0])
                #         # relations.append("ref: "+app_table.__name__+"."+field.name+" > "+str(field.related_model.__name__)+"."+field.to_fields[0])
                #     else:
                #         # _, related_field = field.related_fields[0]
                #         print("ref: "+app_table.__name__+"."+field.name+" > "+str(field.related_model.__name__)+"."+related_field.name)
                #         # relations.append("ref: "+app_table.__name__+"."+field.name+" > "+str(field.related_model.__name__)+"."+related_field.name)
                # else:
                #     related_field = ""
                #     for keey in field.related_model.__dict__.keys():
                #         valuee = field.related_model.__dict__[keey]
                #         if isinstance(valuee, models.query_utils.DeferredAttribute):
                #             related_field = valuee.__dict__['field'].name
                #             break
                #     relations.append("ref: " + app_table.__name__ + "." + field.name + " > " + str(field.related_model.__name__) + "." + related_field)

        for table_name, table in tables.items():
            # if not table_name == "Shipping":
            #     continue
            print("Table {} {{".format(table_name))
            for field_name, field in table["fields"].items():
                print("  {} {} {}".format(field_name, field["type"], self.get_field_notes(field)))
            print("}\n")
