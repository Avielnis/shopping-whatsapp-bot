import re

from core.models import Action, ParsedCommand

_SPLIT_RE = re.compile(r"[,\s]+")


def _split_items(text: str) -> list[str]:
    return [item for item in _SPLIT_RE.split(text.strip()) if item]


def parse(text: str) -> ParsedCommand:
    text = text.strip()

    if text == "רשימה":
        return ParsedCommand(Action.LIST)
    if text in ("עזרה", "פקודות"):
        return ParsedCommand(Action.HELP)
    if text in ("אתר הרשימה", "אתר רשימה"):
        return ParsedCommand(Action.SITE)
    if text in ("נקה", "מחק הכל"):
        return ParsedCommand(Action.CLEAR)
    if text.startswith("בטל סימון"):
        return ParsedCommand(Action.UNMARK, _split_items(text[len("בטל סימון"):]))
    if text.startswith("סמן"):
        return ParsedCommand(Action.MARK, _split_items(text[len("סמן"):]))
    if text.startswith("מחק"):
        return ParsedCommand(Action.REMOVE, _split_items(text[len("מחק"):]))

    return ParsedCommand(Action.ADD, _split_items(text))
