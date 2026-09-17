"""Bot Session darajasidagi middleware'lar - barcha chiquvchi Telegram API
so'rovlariga (xabar/fayl yuborish va h.k.) bir joydan ta'sir qiladi."""
import asyncio
import logging

from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter

logger = logging.getLogger(__name__)


class FloodControlMiddleware(BaseRequestMiddleware):
    """
    Telegram "flood control" (429 - juda tez-tez so'rov yuborilganda) va
    vaqtinchalik tarmoq xatoliklarida avtomatik qayta urinadi.

    Ko'p foydalanuvchi (masalan 1000 kishi) bir vaqtda botga murojaat qilganda
    Telegram javoblarni sekinlashtirishi mumkin - bu middleware'siz bunday
    xabarlar xatolik bilan yo'qolib ketardi. Bot.py'da bir marta ulanadi va
    har bir chiqish so'rovi (sendMessage, sendDocument va h.k.) uchun ishlaydi.
    """

    def __init__(self, max_retries: int = 5) -> None:
        self.max_retries = max_retries

    async def __call__(self, make_request, bot, method):
        for attempt in range(self.max_retries):
            try:
                return await make_request(bot, method)
            except TelegramRetryAfter as e:
                wait_for = e.retry_after + 0.5
                logger.warning(
                    "Telegram flood-control: %s so'rovi uchun %.1f soniya kutilmoqda",
                    type(method).__name__,
                    wait_for,
                )
                await asyncio.sleep(wait_for)
            except TelegramNetworkError:
                if attempt == self.max_retries - 1:
                    raise
                delay = 1.5 * (attempt + 1)
                logger.warning(
                    "Tarmoq xatoligi (%s), %.1f soniyadan keyin qayta uriniladi (urinish %d/%d)",
                    type(method).__name__,
                    delay,
                    attempt + 1,
                    self.max_retries,
                )
                await asyncio.sleep(delay)
        # oxirgi urinish - xato bo'lsa tabiiy ravishda yuqoriga otiladi
        return await make_request(bot, method)
