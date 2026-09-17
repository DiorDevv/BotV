"""Handlerlar orasida umumiy yordamchi funksiyalar."""
from datetime import datetime

from criteria import QUESTION_ORDER, QUESTIONS
from services.sheets import HEADERS


def build_row(data: dict, status: str, stage_label: str = "", cv_link: str = "") -> dict:
    """
    FSM'da to'plangan javoblardan Google Sheets qatoriga mos dict yasaydi.

    status: "accepted" yoki "rejected"
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
    # HEADERS bo'yicha tartiblangan bo'lishini kafolatlaymiz (yetishmasa bo'sh)
    return {h: row.get(h, "") for h in HEADERS}


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
