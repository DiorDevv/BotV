"""Google Sheets bilan ishlash: nomzodlar arxivi."""
import asyncio
import logging

import gspread
from google.oauth2.service_account import Credentials

from config import config
from services import fallback

logger = logging.getLogger(__name__)

HEADERS = [
    "Sana/Vaqt",
    "Telegram username",
    "Telegram ID",
    "Til",
    "Yosh javobi",
    "Ta'lim yo'nalishi javobi",
    "Ilmiy daraja javobi",
    "Kurs javobi",
    "Ta'lim shakli javobi",
    "Holat",
    "Rad etilgan bosqich",
    "CV Drive havolasi",
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_worksheet = None


def _get_credentials() -> Credentials:
    creds = Credentials.from_service_account_file(
        config.GOOGLE_SERVICE_ACCOUNT_JSON_PATH, scopes=SCOPES
    )
    if config.GOOGLE_IMPERSONATE_EMAIL:
        creds = creds.with_subject(config.GOOGLE_IMPERSONATE_EMAIL)
    return creds


def _get_worksheet():
    global _worksheet
    if _worksheet is not None:
        return _worksheet
    client = gspread.authorize(_get_credentials())
    sheet = client.open_by_key(config.GOOGLE_SHEET_ID)
    ws = sheet.sheet1
    existing_header = ws.row_values(1)
    if existing_header != HEADERS:
        ws.update("A1", [HEADERS])
    _worksheet = ws
    return ws


def _append_row_sync(row: dict) -> None:
    ws = _get_worksheet()
    values = [str(row.get(h, "")) for h in HEADERS]
    ws.append_row(values, value_input_option="USER_ENTERED")


def _get_all_records_sync() -> list[dict]:
    ws = _get_worksheet()
    return ws.get_all_records()


async def append_row_with_fallback(row: dict) -> None:
    """Sheets'ga yozishga urinadi; xato bo'lsa mahalliy faylga fallback qiladi."""
    try:
        await asyncio.to_thread(_append_row_sync, row)
    except Exception:
        logger.exception("Google Sheets'ga yozishda xatolik, fallback faylga yozilmoqda")
        await fallback.append_fallback(row)


async def get_all_records() -> list[dict]:
    return await asyncio.to_thread(_get_all_records_sync)
