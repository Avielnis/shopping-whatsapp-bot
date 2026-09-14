from dataclasses import dataclass, field
from enum import Enum, auto


class Action(Enum):
    ADD = auto()
    REMOVE = auto()
    MARK = auto()
    UNMARK = auto()
    LIST = auto()
    CLEAR = auto()
    HELP = auto()


@dataclass
class ParsedCommand:
    action: Action
    items: list[str] = field(default_factory=list)
