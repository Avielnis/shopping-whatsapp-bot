"""Deterministic keyword -> emoji lookup for shopping items. No AI involved:
plain dictionary matching, same input always gives the same output."""

_EMOJI_BY_KEYWORD = {
    "חלב": "🥛",
    "גבינה": "🧀",
    "יוגורט": "🥣",
    "חמאה": "🧈",
    "ביצים": "🥚",
    "לחם": "🍞",
    "פיתה": "🫓",
    "חלה": "🍞",
    "עוף": "🍗",
    "בשר": "🥩",
    "נקניק": "🌭",
    "דג": "🐟",
    "טונה": "🐟",
    "סלמון": "🐟",
    "עגבניות": "🍅",
    "עגבניה": "🍅",
    "מלפפון": "🥒",
    "מלפפונים": "🥒",
    "בצל": "🧅",
    "שום": "🧄",
    "תפוח אדמה": "🥔",
    "תפוחי אדמה": "🥔",
    "תפוח": "🍎",
    "תפוחים": "🍎",
    "בננה": "🍌",
    "בננות": "🍌",
    "תות": "🍓",
    "תותים": "🍓",
    "ענבים": "🍇",
    "לימון": "🍋",
    "אבוקדו": "🥑",
    "גזר": "🥕",
    "פלפל": "🫑",
    "חסה": "🥬",
    "תירס": "🌽",
    "אורז": "🍚",
    "פסטה": "🍝",
    "קמח": "🌾",
    "סוכר": "🧂",
    "מלח": "🧂",
    "שמן": "🫒",
    "קפה": "☕",
    "תה": "🍵",
    "מים": "💧",
    "מיץ": "🧃",
    "קולה": "🥤",
    "יין": "🍷",
    "בירה": "🍺",
    "שוקולד": "🍫",
    "עוגיות": "🍪",
    "חטיף": "🍿",
    "חטיפים": "🍿",
    "גלידה": "🍦",
    "דבש": "🍯",
    "טחינה": "🥜",
    "חומוס": "🧆",
    "נייר טואלט": "🧻",
    "מגבות נייר": "🧻",
    "סבון": "🧼",
    "שמפו": "🧴",
    "מרכך": "🧴",
    "אקונומיקה": "🧴",
    "אבקת כביסה": "🧺",
    "חיתולים": "🧷",
}

_DEFAULT_EMOJI = "🛒"


def emoji_for(name: str) -> str:
    words = name.split()
    for word in words:
        if word in _EMOJI_BY_KEYWORD:
            return _EMOJI_BY_KEYWORD[word]

    for keyword in sorted(_EMOJI_BY_KEYWORD, key=len, reverse=True):
        if keyword in name:
            return _EMOJI_BY_KEYWORD[keyword]

    return _DEFAULT_EMOJI


def label(name: str) -> str:
    return f"{emoji_for(name)} {name}"
