"""Loads and validates configuration from environment variables (.env)."""
import logging
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)


def _parse_admin_ids(raw: str) -> list[int]:
    ids: list[int] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            ids.append(int(chunk))
        except ValueError:
            logger.warning("ADMIN_CHAT_IDS ichida noto'g'ri qiymat e'tiborga olinmadi: %r", chunk)
    return ids


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_CHAT_IDS: list[int] = _parse_admin_ids(os.getenv("ADMIN_CHAT_IDS", ""))

    GOOGLE_SERVICE_ACCOUNT_JSON_PATH: str = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_JSON_PATH", "./credentials.json"
    )
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
    GOOGLE_DRIVE_FOLDER_ID: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
    # Optional: domain-wide delegation - service account impersonates a real
    # Google Workspace user so uploaded files have storage quota/ownership.
    GOOGLE_IMPERSONATE_EMAIL: str | None = os.getenv("GOOGLE_IMPERSONATE_EMAIL") or None

    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: str = os.getenv("SMTP_PORT", "587")
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")
    NOTIFY_EMAIL_TO: str = os.getenv("NOTIFY_EMAIL_TO", "")

    FALLBACK_LOG_PATH: Path = Path(os.getenv("FALLBACK_LOG_PATH", "./fallback_log.jsonl"))
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", "./logs"))
    TMP_DIR: Path = Path(os.getenv("TMP_DIR", "./tmp"))

    def validate(self) -> None:
        if not self.BOT_TOKEN:
            raise RuntimeError("BOT_TOKEN .env faylida ko'rsatilmagan.")
        if not self.ADMIN_CHAT_IDS:
            logger.warning(
                "ADMIN_CHAT_IDS bo'sh - hech kim /stats, /export ishlata olmaydi va "
                "Telegram bildirishnomalari yuborilmaydi."
            )
        if not self.GOOGLE_SHEET_ID:
            logger.warning("GOOGLE_SHEET_ID ko'rsatilmagan - Sheets integratsiyasi ishlamaydi.")


config = Config()
