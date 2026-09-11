from django_dbml.utils import choices_to_markdown_table, cleanup_docstring, to_snake_case


def test_to_snake_case_preserves_common_initialisms() -> None:
    assert to_snake_case("GenericIPAddressField") == "generic_ip_address_field"
    assert to_snake_case("UUIDField") == "uuid_field"
    assert to_snake_case("URLField") == "url_field"
    assert to_snake_case("JSONField") == "json_field"


def test_cleanup_docstring_removes_incidental_indentation() -> None:
    docstring = "\n    Catalog entry.\n\n    Second paragraph.\n    "

    assert cleanup_docstring(docstring) == "Catalog entry.\n\nSecond paragraph."


def test_choices_to_markdown_table_renders_a_header_and_one_row_per_choice() -> None:
    table = choices_to_markdown_table([("draft", "Draft"), ("published", "Published")])

    assert table.splitlines() == [
        "| Value | Display |",
        "| -------- | ------- |",
        "|draft|Draft|",
        "|published|Published|",
    ]


def test_choices_to_markdown_table_handles_an_empty_choice_list() -> None:
    assert choices_to_markdown_table([]).splitlines() == ["| Value | Display |", "| -------- | ------- |"]
