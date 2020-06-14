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
        allowed_types = ["ForeignKey", "ManyToManyField"]
        for field_type in models.__all__:
            if "Field" not in field_type and field_type not in allowed_types:
                continue

            all_fields[field_type] = to_snake_case(
                field_type.replace("Field", ""),
            )
        
        ignore_types = (
            models.fields.reverse_related.ManyToOneRel, 
            models.fields.reverse_related.ManyToManyRel,
        )

        tables = {}
        app_tables = apps.get_models()
        for app_table in app_tables:
            if not app_table._meta.app_label == "core":
                continue
            table_name = app_table.__name__
            tables[table_name] = {
                "fields": {},
                "relations": []
            }
            
            for field in app_table._meta.get_fields():
                if isinstance(field, ignore_types):
                    continue
                
                field_attributes = list(dir(field))

                # print(table_name, field, type(field))
                if isinstance(field, models.fields.related.OneToOneField):
                    tables[table_name]["relations"].append({
                        "type": "one_to_one",
                        "table_from": field.related_model.__name__,
                        "table_from_field": field.target_field.name,
                        "table_to": table_name,
                        "table_to_field": field.name,
                    })

                elif isinstance(field, models.fields.related.ForeignKey):
                    tables[table_name]["relations"].append({
                        "type": "one_to_many",
                        "table_from": field.related_model.__name__,
                        "table_from_field": field.target_field.name,
                        "table_to": table_name,
                        "table_to_field": field.name,
                    })

                elif isinstance(field, models.fields.related.ManyToManyField):
                    table_name_m2m = field.m2m_db_table()
                    if table_name_m2m not in tables.keys():
                        tables[table_name_m2m] = {
                            "fields": {},
                            "relations": []
                        }

                    tables[table_name_m2m]["relations"].append({
                        "type": "one_to_many",
                        "table_from": table_name_m2m,
                        "table_from_field": field.m2m_column_name(),
                        "table_to": field.model.__name__,
                        "table_to_field": field.m2m_target_field_name(),
                    })
                    tables[table_name_m2m]["relations"].append({
                        "type": "one_to_many",
                        "table_from": table_name_m2m,
                        "table_from_field": field.m2m_reverse_name(),
                        "table_to": field.related_model.__name__,
                        "table_to_field": field.m2m_target_field_name(),
                    })
                    tables[table_name_m2m]["fields"][field.m2m_reverse_name()] = {
                        "pk": True,
                        "type": "auto",
                    }

                    tables[table_name_m2m]["fields"][field.m2m_column_name()] = {
                        "pk": True,
                        "type": "auto",
                    }
                    
                    # print(json.dumps(dir(field), indent=4))
                    # print(json.dumps(tables[table_name_m2m], indent=4))
                    # print(field.get_internal_type())
                    # print('related_model', field.related_model)
                    # print('model', field.model)
                    print('m2m_column_name', field.m2m_column_name())
                    print('m2m_db_table', field.m2m_db_table())
                    print('m2m_field_name', field.m2m_field_name())
                    print('m2m_reverse_field_name', field.m2m_reverse_field_name())
                    print('m2m_reverse_name', field.m2m_reverse_name())
                    print('m2m_reverse_target_field_name', field.m2m_reverse_target_field_name())
                    print('m2m_target_field_name', field.m2m_target_field_name())
                    continue
                    
                
                tables[table_name]["fields"][field.name] = {
                    "type": all_fields.get(type(field).__name__),
                }

                if "help_text" in field_attributes:
                    tables[table_name]["fields"][field.name]["note"] = field.help_text

                if "null" in field_attributes and field.null is True:
                    tables[table_name]["fields"][field.name]["null"] = True

                if "primary_key" in field_attributes and field.primary_key is True:
                    tables[table_name]["fields"][field.name]["pk"] = True

                if "unique" in field_attributes and field.unique is True:
                    tables[table_name]["fields"][field.name]["unique"] = True

                # if isinstance(field, models.ManyToManyField):
                #     # for d in dir(field):
                #     #     if not 'field' in d:
                #     #         continue
                #     #     print(d)
                #     # print(table_name, field.target_field.name)
                #     # print(table_name, field.related_model.__name__)
                #     print("M2M", "ref: {}.{} > {}.{}".format(
                #         table_name,
                #         field.name,
                #         field.related_model.__name__,
                #         field.target_field.name,
                #     ))
                #     # print("ref: "+app_table.__name__+"."+field.name+" > "+str(field.related_model.__name__)+"."+related_field.name)
                #     # print(tables[table_name]["fields"])
                #     # print("ref: "+app_table.__name__+"."+field.name+" > "+str(field.related_model.__name__))
                #     # break
                #     # if "related_fields" in dir(field):
                #     #     print("ref: "+app_table.__name__+"."+field.name+" > "+str(field.related_model.__name__)+"."+related_field.name)
                #     # relations.append("ref: "+app_table.__name__+"."+field.name+" > "+str(field.related_model.__name__)+"."+field.to_fields[0])
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
        # return
        for table_name, table in tables.items():
            print("Table {} {{".format(table_name))
            for field_name, field in table["fields"].items():
                print("  {} {} {}".format(field_name, field["type"], self.get_field_notes(field)))
            print("}")

            for relation in table["relations"]:
                if relation['type'] == 'one_to_many':
                    print("ref: {}.{} > {}.{}".format(
                        relation["table_to"],
                        relation["table_to_field"],
                        relation["table_from"],
                        relation["table_from_field"],
                    ))

                if relation['type'] == 'one_to_one':
                    print("ref: {}.{} - {}.{}".format(
                        relation["table_to"],
                        relation["table_to_field"],
                        relation["table_from"],
                        relation["table_from_field"],
                    ))
            print("\n")
