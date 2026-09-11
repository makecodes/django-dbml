from unittest.mock import patch

from django_dbml.core.options import GenerationOptions
from django_dbml.core.renderer import DbmlRenderer
from django_dbml.core.schema import FieldDefinition


def default_renderer() -> DbmlRenderer:
    return DbmlRenderer(GenerationOptions())


def test_callable_defaults_are_rendered_as_a_qualified_call() -> None:
    assert default_renderer().format_default(dict) == "builtins.dict()"


def test_callable_defaults_without_a_module_fall_back_to_the_bare_name() -> None:
    with patch("django_dbml.core.renderer.inspect.getmodule", return_value=None):
        assert default_renderer().format_default(dict) == "dict()"


def test_string_defaults_are_quoted_and_other_values_pass_through() -> None:
    renderer = default_renderer()

    assert renderer.format_default("draft") == '"draft"'
    assert renderer.format_default(0) == 0
    assert renderer.format_default(True) is True


def test_field_without_attributes_still_states_nullability() -> None:
    assert default_renderer().render_field_attributes(FieldDefinition(type="char")) == "[not null]"


def test_field_attributes_are_emitted_in_a_stable_order() -> None:
    field = FieldDefinition(type="char", note="Label", pk=True, unique=True, default="draft", null=True)

    assert default_renderer().render_field_attributes(field) == "[note: '''Label''', pk, unique, default:`\"draft\"`, null]"


def test_single_quotes_in_notes_are_rewritten_so_they_cannot_close_the_block() -> None:
    field = FieldDefinition(type="char", note="the author's name")

    assert default_renderer().render_field_attributes(field) == "[note: '''the author\"s name''', not null]"


def test_multiline_notes_are_rendered_as_a_block() -> None:
    field = FieldDefinition(type="char", note="first\nsecond")

    assert default_renderer().render_field_attributes(field) == "[note: '''\nfirst\nsecond\n''', not null]"
