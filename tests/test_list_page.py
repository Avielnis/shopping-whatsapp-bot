import pytest

from core.shopping_list import ShoppingListService
from frontends.list_page import create_list_page_app


@pytest.fixture
def service():
    service = ShoppingListService(":memory:")
    service.add_items(["חלב", "לחם"])
    return service


@pytest.fixture
def app(service):
    return create_list_page_app(service)


def test_page_loads(app):
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert "רשימת קניות" in response.get_data(as_text=True)


def test_data_endpoint_lists_pending_and_collected(app, service):
    service.mark_collected(["לחם"])
    body = app.test_client().get("/data").get_json()
    assert body["pending"] == [{"name": "חלב", "emoji": "🥛"}]
    assert body["collected"] == [{"name": "לחם", "emoji": "🍞"}]


def test_toggle_checked_marks_item_collected(app, service):
    app.test_client().post("/toggle", data={"name": "חלב", "checked": "on"})
    pending, collected = service.get_list()
    assert pending == ["לחם"] and collected == ["חלב"]


def test_toggle_unchecked_unmarks_item(app, service):
    service.mark_collected(["חלב"])
    app.test_client().post("/toggle", data={"name": "חלב"})
    pending, collected = service.get_list()
    assert "חלב" in pending and collected == []


def test_add_splits_multiple_items(app, service):
    app.test_client().post("/add", data={"text": "ביצים, גבינה"})
    pending, _ = service.get_list()
    assert "ביצים" in pending and "גבינה" in pending
