"""Handlerlar orasida umumiy yordamchi funksiyalar."""
from datetime import datetime

from criteria import QUESTION_ORDER, QUESTIONS
from services.sheets import HEADERS


def build_row(
    data: dict, status: str, stage_label: str = "", cv_link: str = "", cv_file_id: str = ""
) -> dict:
    """
    FSM'da to'plangan javoblardan Google Sheets qatoriga mos dict yasaydi.

    status: "accepted" yoki "rejected"
    cv_file_id: Telegramning ichki fayl ID'si - faqat mahalliy fallback_log.jsonl
        uchun saqlanadi (Google Sheets ustunlari o'zgarmasdan qoladi), admin panel
        Google'siz ham CV faylini qayta yuborishi uchun ishlatiladi.
    """
    row = {
        "Sana/Vaqt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Telegram username": f"@{data['tg_username']}" if data.get("tg_username") else "yo'q",
        "Telegram ID": data.get("tg_id", ""),
        "Til": data.get("lang", ""),
        "Holat": "✅ Mos" if status == "accepted" else "❌ Mos emas",
        "Rad etilgan bosqich": stage_label,
        "CV Drive havolasi": cv_link,
    }
    for key in QUESTION_ORDER:
        row[QUESTIONS[key]["sheet_column"]] = data.get(key, "")
    # HEADERS bo'yicha tartiblangan bo'lishini kafolatlaymiz (yetishmasa bo'sh).
    # Google Sheets yozuvi faqat shu ustunlarni ishlatadi, ortiqcha kalitlarni e'tiborsiz
    # qoldiradi - shuning uchun _cv_file_id shu yerga xavfsiz qo'shiladi.
    result = {h: row.get(h, "") for h in HEADERS}
    if cv_file_id:
        result["_cv_file_id"] = cv_file_id
    return result


def build_admin_notification_text(data: dict, cv_link: str) -> str:
    lines = [
        "✅ Yangi mos nomzod!",
        "",
        f"Ism/username: @{data['tg_username']}" if data.get("tg_username") else "Username: yo'q",
        f"Telegram ID: {data.get('tg_id', '')}",
        f"Til: {data.get('lang', '')}",
        f"Ariza vaqti: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "Javoblar:",
    ]
    for key in QUESTION_ORDER:
        label = QUESTIONS[key]["sheet_column"]
        lines.append(f"  • {label}: {data.get(key, '')}")
    if cv_link:
        lines.append("")
        lines.append(f"CV (Google Drive): {cv_link}")
    return "\n".join(lines)
