import pytest

from core.assistant import ShoppingListAssistant
from core.shopping_list import ShoppingListService


@pytest.fixture
def assistant():
    return ShoppingListAssistant(ShoppingListService(":memory:"))


def test_add_items(assistant):
    reply = assistant.handle_message("חלב, לחם")
    assert "נוספו" in reply and "חלב" in reply and "לחם" in reply


def test_add_duplicate_item_is_a_noop(assistant):
    assistant.handle_message("חלב")
    reply = assistant.handle_message("חלב")
    assert "כבר ברשימה" in reply


def test_readding_collected_item_restores_it(assistant):
    assistant.handle_message("חלב")
    assistant.handle_message("סמן חלב")
    reply = assistant.handle_message("חלב")
    assert "הוחזרו לרשימה" in reply


def test_remove_existing_item(assistant):
    assistant.handle_message("חלב")
    reply = assistant.handle_message("מחק חלב")
    assert "נמחקו" in reply


def test_remove_missing_item(assistant):
    reply = assistant.handle_message("מחק חלב")
    assert "לא נמצאו" in reply


def test_mark_item_collected(assistant):
    assistant.handle_message("חלב")
    reply = assistant.handle_message("סמן חלב")
    assert "סומנו כנאספו" in reply


def test_mark_already_collected_item(assistant):
    assistant.handle_message("חלב")
    assistant.handle_message("סמן חלב")
    reply = assistant.handle_message("סמן חלב")
    assert "כבר סומנו" in reply


def test_unmark_item(assistant):
    assistant.handle_message("חלב")
    assistant.handle_message("סמן חלב")
    reply = assistant.handle_message("בטל סימון חלב")
    assert "בוטל סימון" in reply


def test_empty_list_message(assistant):
    assert "ריקה" in assistant.handle_message("רשימה")


def test_list_shows_pending_and_collected(assistant):
    assistant.handle_message("חלב")
    assistant.handle_message("לחם")
    assistant.handle_message("סמן לחם")
    reply = assistant.handle_message("רשימה")
    assert "☐ " in reply and "חלב" in reply
    assert "✅ " in reply and "לחם" in reply


def test_list_prefixes_items_with_a_matching_emoji(assistant):
    assistant.handle_message("חלב")
    reply = assistant.handle_message("רשימה")
    assert "🥛 חלב" in reply


def test_clear_empties_the_list(assistant):
    assistant.handle_message("חלב")
    reply = assistant.handle_message("נקה")
    assert "נוקתה" in reply
    assert "ריקה" in assistant.handle_message("רשימה")


def test_help_lists_commands(assistant):
    assert "פקודות" in assistant.handle_message("עזרה")
