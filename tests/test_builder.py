from unittest.mock import patch

import pytest
from django.conf import settings

from django_dbml.core.builder import SchemaBuilder, map_field_type_to_dbml_type
from django_dbml.core.options import GenerationOptions
from django_dbml.core.selection import get_model_group
from tests.testapp.models import Book, Shipment


@pytest.fixture
def builder() -> SchemaBuilder:
    return SchemaBuilder(GenerationOptions())


@pytest.mark.parametrize(
    ("engine", "expected"),
    [
        ("django.db.backends.postgresql", "PostgreSQL"),
        ("django.db.backends.postgresql_psycopg2", "PostgreSQL"),
        ("django.db.backends.sqlite3", "SQLite"),
        ("django.db.backends.mysql", "MySQL"),
        ("django.db.backends.oracle", "Oracle"),
        ("mssql", "Microsoft SQL"),
    ],
)
def test_get_db_type_maps_known_engines(builder: SchemaBuilder, engine: str, expected: str) -> None:
    with patch.object(settings, "DATABASES", {"default": {"ENGINE": engine}}):
        assert builder.get_db_type() == expected


def test_get_db_type_reports_unknown_engines_verbatim(builder: SchemaBuilder) -> None:
    with patch.object(settings, "DATABASES", {"default": {"ENGINE": "vendor.custom.backend"}}):
        assert builder.get_db_type() == "Unknown (vendor.custom.backend)"


def test_get_db_type_does_not_recognize_the_legacy_pyodbc_engine(builder: SchemaBuilder) -> None:
    """Detection matches `mssql`, the ENGINE used by the current mssql-django backend.

    The legacy `sql_server.pyodbc` from django-pyodbc-azure is not recognized and
    falls through to the verbatim fallback. Documented here so the fallback is a
    known limit rather than an accident.
    """

    with patch.object(settings, "DATABASES", {"default": {"ENGINE": "sql_server.pyodbc"}}):
        assert builder.get_db_type() == "Unknown (sql_server.pyodbc)"


def test_get_db_for_read_is_none_without_routers(builder: SchemaBuilder) -> None:
    assert builder.get_db_for_read(Book) is None


def test_get_db_for_read_uses_a_configured_router() -> None:
    with patch.object(settings, "DATABASE_ROUTERS", ["tests.test_builder.ReplicaRouter"]):
        builder = SchemaBuilder(GenerationOptions())
        assert builder.get_db_for_read(Book) == "replica"


class ReplicaRouter:
    """Router used to exercise the `db_for_read` branch of table notes."""

    def db_for_read(self, model, **hints):  # noqa: ARG002
        return "replica"


@pytest.mark.parametrize(
    ("table_name", "expected"),
    [
        ("billing.Invoice", "billing.char_invoice_status"),
        ("billing_invoice", "billing.char_invoice_status"),
        ("invoice", "public.char_invoice_status"),
    ],
)
def test_get_enum_name_derives_a_schema_qualified_name(builder: SchemaBuilder, table_name: str, expected: str) -> None:
    assert builder.get_enum_name(table_name, "status", "char") == expected


def test_table_color_is_stable_per_group_and_empty_when_disabled(builder: SchemaBuilder) -> None:
    assert builder.get_table_color("testapp") == ""

    colored = SchemaBuilder(GenerationOptions(color_by_app=True))
    color = colored.get_table_color("testapp")

    assert color.startswith("#")
    assert len(color) == 7
    assert color == colored.get_table_color("testapp")
    assert color != colored.get_table_color("billing")


def test_field_types_are_derived_from_the_class_name() -> None:
    from django.db.models import BigAutoField, CharField, DateTimeField, ForeignKey, JSONField

    assert map_field_type_to_dbml_type(CharField) == "char"
    assert map_field_type_to_dbml_type(DateTimeField) == "date_time"
    assert map_field_type_to_dbml_type(BigAutoField) == "big_auto"
    assert map_field_type_to_dbml_type(JSONField) == "json"
    # The raw mapper still names the relation class; the builder is what declines
    # to use it for a relation column. See get_field_type.
    assert map_field_type_to_dbml_type(ForeignKey) == "foreign_key"


def test_get_field_type_resolves_relations_to_their_target(builder: SchemaBuilder) -> None:
    assert builder.get_field_type(Book._meta.get_field("author")) == "big_auto"
    assert builder.get_field_type(Shipment._meta.get_field("warehouse")) == "auto"
    assert builder.get_field_type(Shipment._meta.get_field("operator")) == "auto"


def test_get_field_type_leaves_plain_columns_alone(builder: SchemaBuilder) -> None:
    assert builder.get_field_type(Book._meta.get_field("title")) == "char"
    assert builder.get_field_type(Book._meta.get_field("published_at")) == "date_time"


def test_model_group_falls_back_to_the_module_when_there_is_no_package() -> None:
    assert get_model_group(Book) == "testapp"

    class Standalone:
        __module__ = "standalone"

    assert get_model_group(Standalone) == "standalone"
