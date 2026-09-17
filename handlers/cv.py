"""3.6-3.7 bosqichlar: CV so'rash, qabul qilish va bildirishnomalar."""
import logging
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import config
from handlers.common import build_admin_notification_text, build_row
from services import drive, email_service, sheets
from states import Form
from texts import TEXTS

logger = logging.getLogger(__name__)

router = Router()


async def ask_for_cv(message: Message, lang: str) -> None:
    await message.answer(TEXTS[lang]["ask_cv"])


async def _notify_admins(bot: Bot, data: dict, cv_link: str, source_message: Message) -> None:
    text = build_admin_notification_text(data, cv_link)
    for admin_id in config.ADMIN_CHAT_IDS:
        try:
            await bot.send_message(admin_id, text)
            if source_message.document:
                await bot.send_document(admin_id, source_message.document.file_id)
            elif source_message.photo:
                await bot.send_photo(admin_id, source_message.photo[-1].file_id)
        except Exception:
            logger.exception("Admin %s ga bildirishnoma yuborib bo'lmadi", admin_id)


@router.message(StateFilter(Form.waiting_for_cv), F.document | F.photo)
async def handle_cv_file(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")

    if message.document:
        file_id = message.document.file_id
        original_name = message.document.file_name or f"file_{message.document.file_unique_id}"
    else:
        photo = message.photo[-1]
        file_id = photo.file_id
        original_name = f"{photo.file_unique_id}.jpg"

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    tg_id = data.get("tg_id", "unknown")
    safe_name = f"{date_str}_{tg_id}_{original_name}"

    config.TMP_DIR.mkdir(parents=True, exist_ok=True)
    local_path = config.TMP_DIR / safe_name

    try:
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=local_path)
    except TelegramBadRequest as e:
        if "file is too big" in str(e).lower():
            await message.answer(TEXTS[lang]["file_too_large"])
        else:
            logger.exception("CV faylini yuklab olishda Telegram xatoligi")
            await message.answer(TEXTS[lang]["error_generic"])
        return
    except Exception:
        logger.exception("CV faylini yuklab olishda kutilmagan xatolik")
        await message.answer(TEXTS[lang]["error_generic"])
        return

    try:
        cv_link = ""
        try:
            cv_link = await drive.upload_file(local_path, safe_name)
        except Exception:
            logger.exception("CV faylini Google Drive'ga yuklashda xatolik")

        row = build_row(data, "accepted", cv_link=cv_link)
        await sheets.append_row_with_fallback(row)

        await _notify_admins(bot, data, cv_link, message)

        admin_text = build_admin_notification_text(data, cv_link)
        await email_service.send_notification_email(
            admin_text, cv_link, attachment_path=local_path, attachment_filename=original_name
        )
    finally:
        local_path.unlink(missing_ok=True)

    await state.clear()
    await message.answer(TEXTS[lang]["cv_accepted"])


@router.message(StateFilter(Form.waiting_for_cv))
async def handle_cv_invalid(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await message.answer(TEXTS[lang]["need_file"])
