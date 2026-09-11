"""Minimal DBML reader used to assert on generated output structurally.

The package's contract is the rendered text, so tests read that text back
instead of reaching into the intermediate schema. This is an assertion aid, not
a DBML implementation: it understands exactly the constructs the renderer
emits, and nothing else.
"""

import re


TABLE_HEADER = re.compile(r"^Table (?P<name>[^\s\[]+)(?: \[(?P<attributes>[^\]]*)\])? \{$")
TABLE_GROUP_HEADER = re.compile(r"^TableGroup (?P<name>\S+) \{$")
RELATION = re.compile(r"^ref: (?P<left>\S+) (?P<operator>[>-]) (?P<right>\S+)$")

# Notes are triple-quoted and may span lines, both as a table note and inside a
# column's attribute list. Any line with an odd number of delimiters opens or
# closes one.
NOTE_DELIMITER = "'''"


def _skips_note(line: str) -> bool:
    return line.count(NOTE_DELIMITER) % 2 == 1


def parse_tables(dbml: str) -> dict[str, list[str]]:
    """Return the column names each rendered table declares, in emitted order."""

    return {table: list(columns) for table, columns in parse_columns(dbml).items()}


def parse_columns(dbml: str) -> dict[str, dict[str, str]]:
    """Return each rendered table's columns mapped to their declared DBML type."""

    tables: dict[str, dict[str, str]] = {}
    current: str | None = None
    inside_note = False
    inside_indexes = False

    for raw_line in dbml.splitlines():
        line = raw_line.strip()

        if inside_note:
            if NOTE_DELIMITER in line:
                inside_note = False
            continue

        if current is None:
            header = TABLE_HEADER.match(line)
            if header:
                current = header.group("name")
                tables[current] = {}
            continue

        if inside_indexes:
            if line == "}":
                inside_indexes = False
            continue

        if line == "indexes {":
            inside_indexes = True
            continue

        if line == "}":
            current = None
            continue

        if not line or line.startswith("Note:"):
            inside_note = _skips_note(line)
            continue

        name, _, remainder = line.partition(" ")
        tables[current][name] = remainder.split(maxsplit=1)[0] if remainder else ""
        inside_note = _skips_note(line)

    return tables


def parse_table_attributes(dbml: str) -> dict[str, str]:
    """Return the bracketed header attributes of each table, when present."""

    attributes = {}
    for raw_line in dbml.splitlines():
        header = TABLE_HEADER.match(raw_line.strip())
        if header and header.group("attributes"):
            attributes[header.group("name")] = header.group("attributes")
    return attributes


def parse_relations(dbml: str) -> list[tuple[str, str, str]]:
    """Return every `ref` as a `(left, operator, right)` triple."""

    relations = []
    for raw_line in dbml.splitlines():
        relation = RELATION.match(raw_line.strip())
        if relation:
            relations.append((relation.group("left"), relation.group("operator"), relation.group("right")))
    return relations


def parse_table_groups(dbml: str) -> dict[str, list[str]]:
    """Return the table names listed under each `TableGroup` block."""

    groups: dict[str, list[str]] = {}
    current: str | None = None

    for raw_line in dbml.splitlines():
        line = raw_line.strip()

        if current is None:
            header = TABLE_GROUP_HEADER.match(line)
            if header:
                current = header.group("name")
                groups[current] = []
            continue

        if line == "}":
            current = None
            continue

        if line:
            groups[current].append(line)

    return groups


def split_endpoint(endpoint: str) -> tuple[str, str]:
    """Split a `ref` endpoint into its table name and column name.

    Table names contain dots (`app_label.ModelName`), so only the final segment
    is the column.
    """

    table, _, column = endpoint.rpartition(".")
    return table, column
