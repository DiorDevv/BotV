"""Google Drive bilan ishlash: CV fayllarni yuklash."""
import asyncio
import logging
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]

_service = None


def _get_credentials() -> Credentials:
    creds = Credentials.from_service_account_file(
        config.GOOGLE_SERVICE_ACCOUNT_JSON_PATH, scopes=SCOPES
    )
    if config.GOOGLE_IMPERSONATE_EMAIL:
        creds = creds.with_subject(config.GOOGLE_IMPERSONATE_EMAIL)
    return creds


def _get_service():
    global _service
    if _service is not None:
        return _service
    _service = build("drive", "v3", credentials=_get_credentials(), cache_discovery=False)
    return _service


def _upload_sync(local_path: Path, filename: str) -> str:
    service = _get_service()
    file_metadata = {"name": filename}
    if config.GOOGLE_DRIVE_FOLDER_ID:
        file_metadata["parents"] = [config.GOOGLE_DRIVE_FOLDER_ID]
    media = MediaFileUpload(str(local_path), resumable=False)
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, webViewLink", supportsAllDrives=True)
        .execute()
    )
    return file.get("webViewLink", "")


async def upload_file(local_path: Path, filename: str) -> str:
    """CV faylni Drive papkasiga yuklaydi va ko'rish havolasini qaytaradi."""
    return await asyncio.to_thread(_upload_sync, local_path, filename)
