from core.models import Action
from core.parser import parse


def test_plain_text_is_add_split_on_commas_spaces_newlines():
    command = parse("חלב, לחם\nביצים קמח")
    assert command.action == Action.ADD
    assert command.items == ["חלב", "לחם", "ביצים", "קמח"]


def test_list_command():
    assert parse("רשימה").action == Action.LIST


def test_help_command():
    assert parse("עזרה").action == Action.HELP


def test_clear_command_both_phrasings():
    assert parse("נקה").action == Action.CLEAR
    assert parse("מחק הכל").action == Action.CLEAR


def test_remove_command():
    command = parse("מחק חלב, לחם")
    assert command.action == Action.REMOVE
    assert command.items == ["חלב", "לחם"]


def test_mark_command():
    command = parse("סמן ביצים")
    assert command.action == Action.MARK
    assert command.items == ["ביצים"]


def test_unmark_command():
    command = parse("בטל סימון ביצים")
    assert command.action == Action.UNMARK
    assert command.items == ["ביצים"]
