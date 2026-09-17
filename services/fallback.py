"""Google Sheets vaqtincha ishlamay qolganda ma'lumotni mahalliy faylga yozish."""
import asyncio
import json
import logging
from datetime import datetime

from config import config

logger = logging.getLogger(__name__)


def _append_sync(row: dict) -> None:
    config.FALLBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = dict(row)
    entry["_fallback_saved_at"] = datetime.now().isoformat()
    with config.FALLBACK_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


async def append_fallback(row: dict) -> None:
    try:
        await asyncio.to_thread(_append_sync, row)
    except Exception:
        logger.exception("Fallback faylga ham yozib bo'lmadi - ma'lumot yo'qolishi mumkin: %r", row)


def _read_all_sync() -> list[dict]:
    if not config.FALLBACK_LOG_PATH.exists():
        return []
    records = []
    with config.FALLBACK_LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            entry.pop("_fallback_saved_at", None)
            records.append(entry)
    return records


async def read_all() -> list[dict]:
    """fallback_log.jsonl faylidagi barcha yozuvlarni o'qiydi (Google Sheets o'rniga)."""
    return await asyncio.to_thread(_read_all_sync)
