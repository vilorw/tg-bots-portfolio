import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str
    ADMIN_CHAT_ID: int

    @classmethod
    def load(cls) -> 'Config':
        token = os.getenv("BOT_TOKEN")
        admin_id = os.getenv("ADMIN_CHAT_ID")
        
        if not token or not admin_id:
            raise ValueError("КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN или ADMIN_CHAT_ID не заданы в .env")
        
        return cls(BOT_TOKEN=token, ADMIN_CHAT_ID=int(admin_id))

# Лимиты валидации
class Limits:
    NAME_MIN = 2
    NAME_MAX = 50
    COMMENT_MAX = 500

try:
    config = Config.load()
except Exception as e:
    exit(print(e))