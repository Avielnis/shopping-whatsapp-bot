import logging
from collections import OrderedDict
from datetime import datetime

import segno
from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv, event

from core.assistant import BOT_LABEL, ShoppingListAssistant

log = logging.getLogger(__name__)

_MAX_SEEN_CHATS = 20


class WhatsAppClient:
    """The only module that knows about neonize/WhatsApp. It filters messages
    down to the one allowed chat and hands raw text to the assistant."""

    def __init__(self, assistant: ShoppingListAssistant, session_path: str, allowed_chat_jid: str):
        self._assistant = assistant
        self.allowed_chat_jid = allowed_chat_jid
        self.is_connected = False
        self.qr_data_uri: str | None = None
        self.seen_chats: "OrderedDict[str, str]" = OrderedDict()  # jid -> last-seen timestamp
        self._client = NewClient(session_path)
        self._client.event(ConnectedEv)(self._on_connected)
        self._client.event(MessageEv)(self._on_message)
        self._client.event.qr(self._on_qr)

    def run(self):
        self._client.connect()
        event.wait()

    def _on_qr(self, _client, data_qr: bytes):
        self.qr_data_uri = segno.make_qr(data_qr).png_data_uri(scale=6)
        self.is_connected = False
        log.info("קוד QR חדש מוכן לסריקה - זמין בדף הניהול (/whatsapp)")

    def _on_connected(self, _client, _event):
        self.is_connected = True
        self.qr_data_uri = None
        log.info("מחובר לוואטסאפ")

    def _remember_chat(self, chat: str):
        self.seen_chats[chat] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.seen_chats.move_to_end(chat)
        while len(self.seen_chats) > _MAX_SEEN_CHATS:
            self.seen_chats.popitem(last=False)

    def _on_message(self, client: NewClient, message: MessageEv):
        text = message.Message.conversation or message.Message.extendedTextMessage.text
        if not text:
            return
        if text.startswith(BOT_LABEL):
            return  # the bot's own message looping back in (multi-device echo)

        chat_jid = message.Info.MessageSource.Chat
        chat = f"{chat_jid.User}@{chat_jid.Server}"
        self._remember_chat(chat)

        if not self.allowed_chat_jid:
            log.info("צ'אט זוהה: %s (הגדר ALLOWED_CHAT_JID כדי להפעיל את הבוט עליו)", chat)
            return
        if chat != self.allowed_chat_jid:
            return

        sender_jid = message.Info.MessageSource.Sender
        sender = f"{sender_jid.User}@{sender_jid.Server}"
        log.info("התקבל מ-%s: %s", sender, text)

        reply = self._assistant.handle_message(text)
        client.reply_message(reply, message)
        log.info("נשלח: %s", reply.replace("\n", " | "))
