from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from tests.dbml_parser import (
    parse_relations,
    parse_table_attributes,
    parse_table_groups,
    parse_tables,
    split_endpoint,
)


pytestmark = pytest.mark.django_db


def render_dbml(*app_labels: str, **options: object) -> str:
    buffer = StringIO()
    call_command("dbml", *app_labels, stdout=buffer, **options)
    return buffer.getvalue()


def test_dbml_command_generates_project_block_and_relations() -> None:
    output = render_dbml(
        add_project_name="Library",
        add_project_notes="Generated for tests.",
        disable_update_timestamp=True,
    )

    assert 'Project "Library"' in output
    assert "Table testapp.Author {" in output
    assert "Table testapp.AuthorProfile {" in output
    assert "Table testapp.Book {" in output
    assert "Table testapp.Tag {" in output
    assert "Table testapp.book_tags {" in output
    assert "enum testapp.char_book_status {" in output
    assert "ref: testapp.Book.author_id > testapp.Author.id" in output
    assert "ref: testapp.AuthorProfile.author_id - testapp.Author.id" in output
    assert "ref: testapp.Tag.id > testapp.book_tags.tag_id" in output
    assert "*DB comment: Stores books*" in output
    assert "Shown in catalogs" in output


def test_dbml_command_includes_related_models_for_specific_model_selection() -> None:
    output = render_dbml(
        "testapp.Book",
        add_project_name="Library",
        add_project_notes="Generated for tests.",
        disable_update_timestamp=True,
    )

    assert "Table testapp.Book {" in output
    assert "Table testapp.Author {" in output
    assert "Table testapp.Tag {" in output
    assert "Table testapp.book_tags {" in output
    assert "Table testapp.AuthorProfile {" not in output


def test_dbml_command_writes_to_output_file(tmp_path) -> None:
    output_file = tmp_path / "schema.dbml"

    call_command(
        "dbml",
        add_project_name="Library",
        add_project_notes="Generated for tests.",
        disable_update_timestamp=True,
        output_file=str(output_file),
    )

    output = output_file.read_text(encoding="utf-8")

    assert output.startswith('Project "Library" {')
    assert "Table testapp.Book {" in output


def test_every_relation_endpoint_references_a_declared_column() -> None:
    """Guards the failure reported in issue #38.

    dbdiagram rejects an entire schema when a ``ref`` names a column its table
    never declared ("Column 'x_id' does not exist in Table 'Y'"), so this holds
    the rule the renderer has to satisfy rather than any one column name.
    """

    output = render_dbml(disable_update_timestamp=True)
    tables = parse_tables(output)
    relations = parse_relations(output)

    assert relations, "expected the fixture app to produce relations"

    for left, _, right in relations:
        for endpoint in (left, right):
            table, column = split_endpoint(endpoint)
            assert table in tables, f"ref {endpoint} points at an undeclared table"
            assert column in tables[table], f"ref {endpoint} points at a column {table} does not declare"


def test_relation_endpoints_hold_when_rendering_database_table_names() -> None:
    """The same invariant, with ``--table_names`` switching every table identifier."""

    output = render_dbml(disable_update_timestamp=True, table_names=True)
    tables = parse_tables(output)

    for left, _, right in parse_relations(output):
        for endpoint in (left, right):
            table, column = split_endpoint(endpoint)
            assert table in tables, f"ref {endpoint} points at an undeclared table"
            assert column in tables[table], f"ref {endpoint} points at a column {table} does not declare"


def test_foreign_key_and_one_to_one_columns_use_the_id_suffix() -> None:
    output = render_dbml("testapp.Shipment", disable_update_timestamp=True)
    columns = parse_tables(output)["testapp.Shipment"]

    assert "warehouse_id" in columns
    assert "operator_id" in columns
    assert "warehouse" not in columns
    assert "operator" not in columns


def test_table_names_option_uses_database_table_names() -> None:
    output = render_dbml("testapp", disable_update_timestamp=True, table_names=True)
    tables = parse_tables(output)

    assert "shipment_record" in tables
    assert "warehouse" in tables
    assert "testapp.Shipment" not in tables
    # The physical table name is only worth noting when it is not already the identifier.
    assert "*table: public.shipment_record*" not in output


def test_model_label_output_notes_the_physical_table() -> None:
    output = render_dbml("testapp.Warehouse", disable_update_timestamp=True)

    assert "Table testapp.Warehouse {" in output
    assert "*table: public.warehouse*" in output


def test_group_by_app_emits_table_groups() -> None:
    output = render_dbml("testapp", disable_update_timestamp=True, group_by_app=True)
    groups = parse_table_groups(output)

    assert "testapp" in groups
    assert "testapp.Book" in groups["testapp"]


def test_color_by_app_gives_every_table_of_an_app_the_same_header_color() -> None:
    output = render_dbml("testapp", disable_update_timestamp=True, color_by_app=True)
    attributes = parse_table_attributes(output)

    assert attributes, "expected --color_by_app to emit header colors"

    colors = set(attributes.values())
    assert len(colors) == 1, f"tables of one app should share a color, got {colors}"
    assert next(iter(colors)).startswith("headercolor: #")


def test_header_colors_are_absent_without_the_option() -> None:
    output = render_dbml("testapp", disable_update_timestamp=True)

    assert parse_table_attributes(output) == {}


def test_project_notes_carry_an_update_timestamp_by_default() -> None:
    output = render_dbml("testapp", add_project_notes="Generated for tests.")

    assert "Last Updated At " in output
    assert "UTC" in output


def test_disable_update_timestamp_removes_it() -> None:
    output = render_dbml("testapp", add_project_notes="Generated for tests.", disable_update_timestamp=True)

    assert "Last Updated At " not in output


def test_default_project_name_and_notes() -> None:
    output = render_dbml("testapp", disable_update_timestamp=True)

    assert 'Project "Django DBML" {' in output
    assert "Generated from Django models." in output


def test_selecting_a_whole_app_by_label() -> None:
    output = render_dbml("testapp", disable_update_timestamp=True)
    tables = parse_tables(output)

    assert "testapp.Book" in tables
    assert "testapp.Warehouse" in tables


def test_unknown_app_label_raises_command_error() -> None:
    with pytest.raises(CommandError):
        render_dbml("no_such_app", disable_update_timestamp=True)


def test_explicit_through_model_is_rendered_instead_of_a_synthesized_join_table() -> None:
    output = render_dbml("testapp", disable_update_timestamp=True)
    tables = parse_tables(output)

    assert "testapp.BookPlacement" in tables
    assert "position" in tables["testapp.BookPlacement"]
    # A synthesized join table is only correct for auto-created through models.
    assert "testapp.book_shelves" not in tables


def test_autogenerated_many_to_many_table_is_marked_as_such() -> None:
    output = render_dbml("testapp", disable_update_timestamp=True)
    tables = parse_tables(output)

    assert tables["testapp.book_tags"] == ["id", "tag_id", "book_id"]
    assert "This is a Many-To-Many linking table autogenerated by Django." in output


def test_choices_become_an_enum_referenced_by_the_column() -> None:
    output = render_dbml("testapp.Book", disable_update_timestamp=True)

    assert "enum testapp.char_book_status {" in output
    assert '"draft" [note: \'\'\'Draft\'\'\']' in output
    assert "status testapp.char_book_status" in output


@override_settings(DATABASE_ROUTERS=["tests.test_builder.ReplicaRouter"])
def test_table_notes_name_the_database_a_router_reads_from() -> None:
    output = render_dbml("testapp.Warehouse", disable_update_timestamp=True)

    assert "*DB: replica, table: public.warehouse*" in output
