from core.emoji_lookup import emoji_for, label


def test_known_item_gets_matching_emoji():
    assert emoji_for("חלב") == "🥛"
    assert emoji_for("לחם") == "🍞"


def test_matches_keyword_inside_a_longer_item_name():
    assert emoji_for("חלב 3%") == "🥛"
    assert emoji_for("עגבניות שרי") == "🍅"


def test_unknown_item_falls_back_to_default_emoji():
    assert emoji_for("קסדת אופניים") == "🛒"


def test_lookup_is_deterministic():
    assert emoji_for("חלב") == emoji_for("חלב")


def test_label_prefixes_name_with_its_emoji():
    assert label("חלב") == "🥛 חלב"
