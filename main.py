import logging
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import Config
from core.assistant import ShoppingListAssistant
from core.shopping_list import ShoppingListService
from frontends.whatsapp_client import WhatsAppClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s %(levelname)s] - %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),  # appends across restarts
        logging.StreamHandler(sys.stdout),
    ],
    force=True,  # override any handlers a dependency (neonize) already attached
)


def main():
    config = Config()
    os.makedirs(os.path.dirname(config.db_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(config.session_path) or ".", exist_ok=True)

    service = ShoppingListService(config.db_path)
    assistant = ShoppingListAssistant(service)
    client = WhatsAppClient(assistant, config.session_path, config.allowed_chat_jid)
    client.run()


if __name__ == "__main__":
    main()
