import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    db_path: str = os.getenv("DB_PATH", "data/shopping_list.db")
    session_path: str = os.getenv("SESSION_PATH", "data/session.db")
    allowed_chat_jid: str = os.getenv("ALLOWED_CHAT_JID", "")
