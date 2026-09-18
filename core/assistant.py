from core.emoji_lookup import label as with_emoji
from core.models import Action
from core.parser import parse
from core.shopping_list import ShoppingListService

BOT_LABEL = "🤖 _בוט_"

HELP_TEXT = (
    "🛒 *פקודות הבוט*\n\n"
    "• שליחת מוצר/ים (מופרדים בפסיק, רווח או שורה חדשה) — הוספה לרשימה\n"
    "• רשימה — הצגת הרשימה\n"
    "• סמן <מוצר> — סימון כנאסף\n"
    "• בטל סימון <מוצר> — ביטול סימון\n"
    "• מחק <מוצר> — מחיקת מוצר מהרשימה\n"
    "• נקה / מחק הכל — ניקוי הרשימה כולה\n"
    "• עזרה — הצגת ההודעה הזו\n\n"
    "ניתן גם להשתמש במספר מהרשימה במקום שם המוצר, למשל: מחק 1"
)


class ShoppingListAssistant:
    def __init__(self, service: ShoppingListService):
        self._service = service

    def handle_message(self, text: str) -> str:
        return f"{BOT_LABEL}\n{self._dispatch(text)}"

    def _dispatch(self, text: str) -> str:
        command = parse(text)

        if command.action == Action.HELP:
            return HELP_TEXT
        if command.action == Action.LIST:
            return self._format_list()
        if command.action == Action.CLEAR:
            self._service.clear_all()
            return self._with_full_list("🧹 הרשימה נוקתה")
        if not command.items:
            return self._with_full_list("לא זיהיתי מוצרים בהודעה 🤔")

        if command.action == Action.ADD:
            added, already_pending, restored = self._service.add_items(command.items)
            reply = self._format_reply(
                [
                    ("✅ נוספו", added),
                    ("↩️ הוחזרו לרשימה", restored),
                    ("⚠️ כבר ברשימה", already_pending),
                ]
            )
            return self._with_full_list(reply)
        if command.action == Action.REMOVE:
            items = self._service.resolve(command.items)
            removed, not_found = self._service.remove_items(items)
            reply = self._format_reply(
                [("🗑️ נמחקו", removed), ("⚠️ לא נמצאו ברשימה", not_found)]
            )
            return self._with_full_list(reply)
        if command.action == Action.MARK:
            items = self._service.resolve(command.items)
            marked, already_collected, not_found = self._service.mark_collected(items)
            reply = self._format_reply(
                [
                    ("✅ סומנו כנאספו", marked),
                    ("⚠️ כבר סומנו", already_collected),
                    ("⚠️ לא נמצאו ברשימה", not_found),
                ]
            )
            return self._with_full_list(reply)
        if command.action == Action.UNMARK:
            items = self._service.resolve(command.items)
            unmarked, not_found = self._service.unmark(items)
            reply = self._format_reply(
                [
                    ("↩️ בוטל סימון עבור", unmarked),
                    ("⚠️ לא נמצאו ברשימה מסומנת", not_found),
                ]
            )
            return self._with_full_list(reply)
        return self._with_full_list("לא הבנתי את ההודעה 🤔")

    def _with_full_list(self, reply: str) -> str:
        return f"{reply}\n\n{self._format_list()}"

    @staticmethod
    def _format_reply(groups: list[tuple[str, list[str]]]) -> str:
        lines = [
            f"{title}: {', '.join(with_emoji(item) for item in items)}"
            for title, items in groups
            if items
        ]
        return "\n".join(lines) if lines else "לא בוצע שינוי"

    def _format_list(self) -> str:
        pending, collected = self._service.get_list()
        if not pending and not collected:
            return "הרשימה ריקה 🎉"
        lines = ["🛒 *רשימת קניות*", ""]
        number = 1
        for name in pending:
            lines.append(f"{number}) {with_emoji(name)}")
            number += 1
        if collected:
            lines.append("")
            for name in collected:
                lines.append(f"{number}) ~{with_emoji(name)}~")
                number += 1
        return "\n".join(lines)
