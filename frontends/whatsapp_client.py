import logging

from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv, event

from core.assistant import ShoppingListAssistant

log = logging.getLogger(__name__)


class WhatsAppClient:
    """The only module that knows about neonize/WhatsApp. It filters messages
    down to the one allowed chat and hands raw text to the assistant."""

    def __init__(self, assistant: ShoppingListAssistant, session_path: str, allowed_chat_jid: str):
        self._assistant = assistant
        self._allowed_chat_jid = allowed_chat_jid
        self._sent_ids: set[str] = set()
        self._client = NewClient(session_path)
        self._client.event(ConnectedEv)(self._on_connected)
        self._client.event(MessageEv)(self._on_message)

    def run(self):
        self._client.connect()
        event.wait()

    def _on_connected(self, _client, _event):
        log.info("מחובר לוואטסאפ")

    def _on_message(self, client: NewClient, message: MessageEv):
        if message.Info.ID in self._sent_ids:
            return  # the bot's own reply looping back in

        chat_jid = message.Info.MessageSource.Chat
        chat = f"{chat_jid.User}@{chat_jid.Server}"
        if not self._allowed_chat_jid:
            log.info("צ'אט זוהה: %s (הגדר ALLOWED_CHAT_JID כדי להפעיל את הבוט עליו)", chat)
            return
        if chat != self._allowed_chat_jid:
            return

        text = message.Message.conversation or message.Message.extendedTextMessage.text
        if not text:
            return

        sender_jid = message.Info.MessageSource.Sender
        sender = f"{sender_jid.User}@{sender_jid.Server}"
        log.info("התקבל מ-%s: %s", sender, text)

        reply = self._assistant.handle_message(text)
        sent = client.reply_message(reply, message)
        if sent is not None:
            self._sent_ids.add(sent.ID)
        log.info("נשלח: %s", reply.replace("\n", " | "))
