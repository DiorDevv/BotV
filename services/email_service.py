"""SMTP orqali mos nomzod haqida bildirishnoma emaili yuborish."""
import logging
from email.message import EmailMessage
from pathlib import Path

import aiosmtplib

from config import config

logger = logging.getLogger(__name__)


def _build_body(candidate_text: str, cv_link: str) -> str:
    lines = [candidate_text]
    if cv_link:
        lines.append(f"\nCV (Google Drive): {cv_link}")
    return "\n".join(lines)


async def send_notification_email(
    candidate_text: str,
    cv_link: str,
    attachment_path: Path | None,
    attachment_filename: str,
) -> None:
    """
    Mos nomzod haqida email yuboradi. SMTP sozlanmagan yoki xatolik yuz
    bersa - istisno tashlamaydi, faqat logga yozadi (email qo'shimcha
    kanal, asosiy oqim - Telegram + Sheets - unga bog'liq bo'lmasligi kerak).
    """
    if not config.SMTP_HOST or not config.NOTIFY_EMAIL_TO:
        logger.info("SMTP sozlanmagan - email bildirishnoma o'tkazib yuborildi")
        return

    try:
        msg = EmailMessage()
        msg["Subject"] = "Yangi mos nomzod arizasi - HR Bot"
        msg["From"] = config.SMTP_FROM or config.SMTP_USER
        msg["To"] = config.NOTIFY_EMAIL_TO
        msg.set_content(_build_body(candidate_text, cv_link))

        if attachment_path and attachment_path.exists():
            content = attachment_path.read_bytes()
            msg.add_attachment(
                content,
                maintype="application",
                subtype="octet-stream",
                filename=attachment_filename,
            )

        await aiosmtplib.send(
            msg,
            hostname=config.SMTP_HOST,
            port=int(config.SMTP_PORT or 587),
            username=config.SMTP_USER or None,
            password=config.SMTP_PASSWORD or None,
            start_tls=True,
        )
        logger.info("Bildirishnoma emaili %s manziliga yuborildi", config.NOTIFY_EMAIL_TO)
    except Exception:
        logger.exception("Bildirishnoma emailini yuborishda xatolik yuz berdi")
