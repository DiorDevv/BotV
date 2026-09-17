"""Admin panel: /start bosganda tugmali menyu, /stats, /export, CV arxivini ko'rish."""
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from openpyxl import Workbook

from config import config
from services import sheets
from texts import TEXTS

logger = logging.getLogger(__name__)

router = Router()

CV_LIST_LIMIT = 15
CANDIDATE_FIELDS = [
    "Sana/Vaqt",
    "Telegram username",
    "Telegram ID",
    "Til",
    "Yosh javobi",
    "Ta'lim yo'nalishi javobi",
    "Ilmiy daraja javobi",
    "Kurs javobi",
    "Ta'lim shakli javobi",
]

# admin_id -> so'nggi ko'rsatilgan "mos" nomzodlar ro'yxati.
# Ro'yxat tugmalaridagi callback_data faqat indeks saqlaydi (64 baytlik limit
# tufayli), shuning uchun haqiqiy yozuvlar shu yerda keshlanadi.
_cv_cache: dict[int, list[dict]] = {}


def is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in config.ADMIN_CHAT_IDS


def _is_admin_message(message: Message) -> bool:
    return is_admin(message.from_user.id if message.from_user else None)


def _is_admin_callback(callback: CallbackQuery) -> bool:
    return is_admin(callback.from_user.id if callback.from_user else None)


def _admin_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistika", callback_data="admin:stats")
    builder.button(text="📁 So'nggi CV'lar", callback_data="admin:cvs")
    builder.button(text="📤 Excel eksport", callback_data="admin:export")
    builder.adjust(1)
    return builder.as_markup()


async def _build_stats_text() -> str:
    records = await sheets.get_all_records()
    total = len(records)
    accepted = sum(1 for r in records if r.get("Holat") == "✅ Mos")
    rejected = total - accepted

    stage_counter = Counter(
        r.get("Rad etilgan bosqich")
        for r in records
        if r.get("Holat") == "❌ Mos emas" and r.get("Rad etilgan bosqich")
    )

    lines = [
        "📊 Statistika",
        f"Jami arizalar: {total}",
        f"Mos nomzodlar: {accepted}",
        f"Mos emas: {rejected}",
    ]
    if stage_counter:
        lines.append("")
        lines.append("Rad etilgan bosqichlar bo'yicha taqsimot:")
        for stage, count in stage_counter.most_common():
            lines.append(f"  • {stage}: {count}")
    return "\n".join(lines)


def _build_xlsx(records: list[dict]) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Nomzodlar"

    headers = list(records[0].keys()) if records else list(sheets.HEADERS)
    ws.append(headers)
    for record in records:
        ws.append([record.get(h, "") for h in headers])

    config.TMP_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"hr_bot_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = config.TMP_DIR / filename
    wb.save(path)
    return path


def _candidate_label(record: dict) -> str:
    username = record.get("Telegram username", "yo'q")
    date = record.get("Sana/Vaqt", "")
    return f"{date} — {username}"


def _candidate_detail_text(record: dict) -> str:
    lines = ["✅ Nomzod ma'lumotlari", ""]
    for field in CANDIDATE_FIELDS:
        lines.append(f"{field}: {record.get(field, '')}")
    cv_link = record.get("CV Drive havolasi", "")
    lines.append("")
    if cv_link:
        lines.append(f"CV (Google Drive): {cv_link}")
    else:
        lines.append(
            "CV havolasi mavjud emas (Google Drive sozlanmagan yoki fayl "
            "ariza vaqtida yuklanmagan)."
        )
    return "\n".join(lines)


async def _cv_list_keyboard() -> tuple[str, object | None, list[dict]]:
    records = await sheets.get_all_records()
    accepted = [r for r in records if r.get("Holat") == "✅ Mos"]
    accepted = list(reversed(accepted))[:CV_LIST_LIMIT]

    if not accepted:
        return "Hozircha mos nomzodlar topilmadi.", None, []

    builder = InlineKeyboardBuilder()
    for idx, record in enumerate(accepted):
        builder.button(text=_candidate_label(record), callback_data=f"admin:cv:{idx}")
    builder.button(text="⬅️ Bosh menyu", callback_data="admin:menu")
    builder.adjust(1)
    return f"So'nggi {len(accepted)} ta mos nomzod:", builder.as_markup(), accepted


# ---- /start (faqat adminlar uchun tugmali menyu) ----------------------------


@router.message(CommandStart(), _is_admin_message)
async def cmd_start_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("👋 Admin panel. Kerakli bo'limni tanlang:", reply_markup=_admin_menu_keyboard())


@router.callback_query(_is_admin_callback, lambda c: c.data == "admin:menu")
async def cb_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer("👋 Admin panel. Kerakli bo'limni tanlang:", reply_markup=_admin_menu_keyboard())


# ---- Statistika ---------------------------------------------------------


@router.message(Command("stats"), _is_admin_message)
async def cmd_stats(message: Message) -> None:
    try:
        text = await _build_stats_text()
    except Exception:
        logger.exception("/stats uchun Sheets'dan ma'lumot olishda xatolik")
        await message.answer(TEXTS["uz"]["error_generic"])
        return
    await message.answer(text, reply_markup=_admin_menu_keyboard())


@router.callback_query(_is_admin_callback, lambda c: c.data == "admin:stats")
async def cb_stats(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        text = await _build_stats_text()
    except Exception:
        logger.exception("/stats (tugma) uchun ma'lumot olishda xatolik")
        await callback.message.answer(TEXTS["uz"]["error_generic"])
        return
    await callback.message.answer(text, reply_markup=_admin_menu_keyboard())


# ---- Excel eksport --------------------------------------------------------


@router.message(Command("export"), _is_admin_message)
async def cmd_export(message: Message) -> None:
    try:
        records = await sheets.get_all_records()
    except Exception:
        logger.exception("/export uchun Sheets'dan ma'lumot olishda xatolik")
        await message.answer(TEXTS["uz"]["error_generic"])
        return

    if not records:
        await message.answer(TEXTS["uz"]["no_data"], reply_markup=_admin_menu_keyboard())
        return

    path = _build_xlsx(records)
    try:
        await message.answer_document(
            FSInputFile(path, filename="hr_bot_export.xlsx"),
            caption="Eksport tayyor.",
            reply_markup=_admin_menu_keyboard(),
        )
    except Exception:
        logger.exception("/export faylini yuborishda xatolik")
        await message.answer(TEXTS["uz"]["error_generic"])
    finally:
        path.unlink(missing_ok=True)


@router.callback_query(_is_admin_callback, lambda c: c.data == "admin:export")
async def cb_export(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        records = await sheets.get_all_records()
    except Exception:
        logger.exception("/export (tugma) uchun ma'lumot olishda xatolik")
        await callback.message.answer(TEXTS["uz"]["error_generic"])
        return

    if not records:
        await callback.message.answer(TEXTS["uz"]["no_data"], reply_markup=_admin_menu_keyboard())
        return

    path = _build_xlsx(records)
    try:
        await callback.message.answer_document(
            FSInputFile(path, filename="hr_bot_export.xlsx"),
            caption="Eksport tayyor.",
            reply_markup=_admin_menu_keyboard(),
        )
    except Exception:
        logger.exception("/export (tugma) faylini yuborishda xatolik")
        await callback.message.answer(TEXTS["uz"]["error_generic"])
    finally:
        path.unlink(missing_ok=True)


# ---- CV arxivini ko'rish ---------------------------------------------------


@router.callback_query(_is_admin_callback, lambda c: c.data == "admin:cvs")
async def cb_cv_list(callback: CallbackQuery) -> None:
    await callback.answer()
    admin_id = callback.from_user.id
    try:
        text, markup, records = await _cv_list_keyboard()
    except Exception:
        logger.exception("CV ro'yxatini olishda xatolik")
        await callback.message.answer(TEXTS["uz"]["error_generic"])
        return
    _cv_cache[admin_id] = records
    await callback.message.answer(text, reply_markup=markup)


@router.callback_query(_is_admin_callback, lambda c: c.data.startswith("admin:cv:"))
async def cb_cv_detail(callback: CallbackQuery) -> None:
    await callback.answer()
    admin_id = callback.from_user.id
    try:
        idx = int(callback.data.split(":", 2)[2])
    except (ValueError, IndexError):
        return

    records = _cv_cache.get(admin_id)
    if not records or idx >= len(records):
        await callback.message.answer(
            "Ro'yxat eskirgan, iltimos qaytadan \"📁 So'nggi CV'lar\" tugmasini bosing.",
            reply_markup=_admin_menu_keyboard(),
        )
        return

    await callback.message.answer(_candidate_detail_text(records[idx]), reply_markup=_admin_menu_keyboard())
