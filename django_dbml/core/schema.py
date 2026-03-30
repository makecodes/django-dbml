from dataclasses import dataclass, field
from typing import Any


UNSET = object()


@dataclass(frozen=True)
class EnumValue:
    value: Any
    display: str


@dataclass(frozen=True)
class RelationDefinition:
    kind: str
    table_from: str
    table_from_field: str
    table_to: str
    table_to_field: str


@dataclass(frozen=True)
class IndexDefinition:
    fields: list[str]
    type: str
    name: str
    unique: bool = False
    pk: bool = False


@dataclass
class FieldDefinition:
    type: str
    note: str = ""
    null: bool = False
    pk: bool = False
    unique: bool = False
    default: Any = UNSET

    @property
    def has_default(self) -> bool:
        return self.default is not UNSET


@dataclass
class TableDefinition:
    name: str
    group: str
    color: str = ""
    fields: dict[str, FieldDefinition] = field(default_factory=dict)
    relations: list[RelationDefinition] = field(default_factory=list)
    indexes: list[IndexDefinition] = field(default_factory=list)
    note: str = ""


@dataclass
class ProjectDefinition:
    name: str
    notes: str
    database_type: str
    include_timestamp: bool
    enums: dict[str, list[EnumValue]] = field(default_factory=dict)
    tables: dict[str, TableDefinition] = field(default_factory=dict)
