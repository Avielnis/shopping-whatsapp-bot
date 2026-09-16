import pytest

from core.shopping_list import ShoppingListService


@pytest.fixture
def service():
    return ShoppingListService(":memory:")


def test_resolve_translates_numbers_to_item_names(service):
    service.add_items(["חלב", "לחם"])
    assert service.resolve(["2", "1"]) == ["לחם", "חלב"]


def test_resolve_leaves_non_numeric_tokens_untouched(service):
    service.add_items(["חלב"])
    assert service.resolve(["גבינה"]) == ["גבינה"]


def test_resolve_leaves_out_of_range_numbers_untouched(service):
    service.add_items(["חלב"])
    assert service.resolve(["9"]) == ["9"]


def test_resolve_numbers_span_pending_then_collected(service):
    service.add_items(["חלב", "לחם"])
    service.mark_collected(["חלב"])
    pending, collected = service.get_list()
    assert pending == ["לחם"]
    assert collected == ["חלב"]
    assert service.resolve(["1", "2"]) == ["לחם", "חלב"]
