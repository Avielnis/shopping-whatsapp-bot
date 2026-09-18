import pytest

from core.assistant import ShoppingListAssistant
from core.shopping_list import ShoppingListService


@pytest.fixture
def assistant():
    return ShoppingListAssistant(ShoppingListService(":memory:"))


def test_add_items(assistant):
    reply = assistant.handle_message("חלב, לחם")
    assert "נוספו" in reply and "חלב" in reply and "לחם" in reply


def test_add_reply_includes_the_full_list(assistant):
    assistant.handle_message("חלב")
    reply = assistant.handle_message("לחם")
    assert "רשימת קניות" in reply
    assert "1) " in reply and "חלב" in reply
    assert "2) " in reply and "לחם" in reply


def test_remove_reply_includes_the_full_list(assistant):
    assistant.handle_message("חלב, לחם")
    reply = assistant.handle_message("מחק חלב")
    assert "רשימת קניות" in reply
    assert "לחם" in reply
    assert "1) " in reply


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


def test_mark_reply_includes_the_full_list(assistant):
    assistant.handle_message("חלב")
    reply = assistant.handle_message("סמן חלב")
    assert "רשימת קניות" in reply


def test_unmark_reply_includes_the_full_list(assistant):
    assistant.handle_message("חלב")
    assistant.handle_message("סמן חלב")
    reply = assistant.handle_message("בטל סימון חלב")
    assert "רשימת קניות" in reply


def test_clear_reply_includes_the_full_list(assistant):
    assistant.handle_message("חלב")
    reply = assistant.handle_message("נקה")
    assert "נוקתה" in reply and "ריקה" in reply


def test_help_reply_does_not_include_the_full_list(assistant):
    assistant.handle_message("חלב")
    reply = assistant.handle_message("עזרה")
    assert "רשימת קניות" not in reply


def test_empty_list_message(assistant):
    assert "ריקה" in assistant.handle_message("רשימה")


def test_list_shows_pending_and_collected(assistant):
    assistant.handle_message("חלב")
    assistant.handle_message("לחם")
    assistant.handle_message("סמן לחם")
    reply = assistant.handle_message("רשימה")
    assert "1) " in reply and "חלב" in reply
    assert "2) ~" in reply and "לחם" in reply


def test_remove_item_by_its_list_number(assistant):
    assistant.handle_message("חלב, לחם")
    reply = assistant.handle_message("מחק 2")
    assert "נמחקו" in reply and "לחם" in reply
    pending, _ = assistant._service.get_list()
    assert pending == ["חלב"]


def test_mark_item_by_its_list_number(assistant):
    assistant.handle_message("חלב, לחם")
    reply = assistant.handle_message("סמן 1")
    assert "סומנו כנאספו" in reply and "חלב" in reply


def test_unmark_item_by_its_list_number(assistant):
    assistant.handle_message("חלב")
    assistant.handle_message("סמן חלב")
    reply = assistant.handle_message("בטל סימון 1")
    assert "בוטל סימון" in reply and "חלב" in reply


def test_out_of_range_number_is_reported_as_not_found(assistant):
    assistant.handle_message("חלב")
    reply = assistant.handle_message("מחק 5")
    assert "לא נמצאו" in reply


def test_collected_items_are_struck_through(assistant):
    assistant.handle_message("חלב")
    assistant.handle_message("סמן חלב")
    reply = assistant.handle_message("רשימה")
    assert "~🥛 חלב~" in reply


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
