from io import StringIO

import pytest
from django.core.management import call_command


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
