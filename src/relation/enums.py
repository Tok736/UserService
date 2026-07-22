from enum import StrEnum, auto


# fmt: off
class StudentSort(StrEnum):
    name_     = "name"
    created   = auto()


class RelationType(StrEnum):
    """Тип связи между людьми"""

    tutor_of  = auto()
    parent_of = auto()


class RelationStatus(StrEnum):
    active    = auto()
    paused    = auto()
    archived  = auto()
# fmt: on
