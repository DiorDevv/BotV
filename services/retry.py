"""Tashqi xizmatlarga (Google Sheets/Drive) chaqiruvlarni vaqtinchalik
xatoliklarda eksponensial kutish bilan qayta urinuvchi yordamchi."""
import asyncio
import logging
import random

logger = logging.getLogger(__name__)


async def retry_sync_call(func, *args, retries: int = 3, base_delay: float = 1.0, **kwargs):
    """
    Sync `func`ni alohida thread'da (asyncio.to_thread) chaqiradi. Xatolik
    bo'lsa eksponensial backoff bilan qayta uriniladi (masalan, Google API
    kvota/vaqtinchalik xatoliklari uchun foydali) - shu bilan ko'p
    foydalanuvchi bir vaqtda ariza yuborganda keraksiz fallback'ga
    tushib qolishning oldini oladi.
    """
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - tashqi xizmat xatoligi, turi oldindan noma'lum
            last_exc = exc
            if attempt == retries - 1:
                break
            delay = base_delay * (2**attempt) + random.uniform(0, 0.5)
            logger.warning(
                "Tashqi chaqiruv muvaffaqiyatsiz (urinish %d/%d): %s - %.1f soniyadan keyin qayta uriniladi",
                attempt + 1,
                retries,
                exc,
                delay,
            )
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc
