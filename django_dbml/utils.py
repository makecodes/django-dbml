import re
from textwrap import dedent


snake_pattern = re.compile(r"(?<!^)(?=[A-Z])")


def to_snake_case(value):
    value = snake_pattern.sub("_", value).lower()
    value = value.replace("i_p_", "ip_").replace("u_r_l", "url").replace("u_u_i_d", "uuid").replace("j_s_o_n", "json")

    return value


def cleanup_docstring(input_docstring: str) -> str:
    """Remove incidental indentation to render notes consistently."""

    return "\n".join([dedent(line) for line in input_docstring.split("\n")]).strip("\n")


def choices_to_markdown_table(choices: list) -> str:
    """Render field choices as a markdown table."""

    lines = ["| Value | Display |", "| -------- | ------- |"]
    for value, display in choices:
        lines.append(f"|{value}|{display}|")

    return "\n".join(lines)
