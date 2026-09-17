"""3.1-3.5 bosqichlar: savol-javob va filtrlash logikasi."""
import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from criteria import QUESTIONS, STATE_KEY_MAP, get_option, is_accepted
from handlers.common import build_row
from keyboards import build_question_keyboard
from services import sheets
from states import Form
from texts import TEXTS

logger = logging.getLogger(__name__)

router = Router()

QUESTION_STATES = [QUESTIONS[key]["state"] for key in QUESTIONS]


async def _current_question_key(state: FSMContext) -> str | None:
    current = await state.get_state()
    return STATE_KEY_MAP.get(current)


@router.callback_query(StateFilter(*QUESTION_STATES), F.data.startswith("ans:"))
async def handle_answer(callback: CallbackQuery, state: FSMContext) -> None:
    key = await _current_question_key(state)
    if key is None:
        await callback.answer()
        return

    try:
        _, cb_key, option_id = callback.data.split(":", 2)
    except ValueError:
        await callback.answer()
        return

    if cb_key != key:
        # eskirgan/mos kelmagan tugma bosilgan - e'tiborsiz qoldiramiz
        await callback.answer()
        return

    question = QUESTIONS[key]
    option = get_option(key, option_id)
    if option is None:
        await callback.answer()
        return

    data = await state.get_data()
    lang = data.get("lang", "uz")
    await callback.answer()

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await state.update_data(**{key: option[lang]})
    data = await state.get_data()

    if not is_accepted(key, option_id):
        await state.clear()
        await callback.message.answer(TEXTS[lang]["reject"])
        row = build_row(data, "rejected", stage_label=question["reject_label"][lang])
        await sheets.append_row_with_fallback(row)
        return

    next_key = question["next"]
    if next_key is None:
        # import shu yerda - aylanma import (cv.py <-> questions.py) oldini olish uchun
        from handlers.cv import ask_for_cv

        await state.set_state(Form.waiting_for_cv)
        await ask_for_cv(callback.message, lang)
        return

    next_question = QUESTIONS[next_key]
    await state.set_state(next_question["state"])
    await callback.message.answer(
        next_question["question"][lang],
        reply_markup=build_question_keyboard(next_key, next_question, lang),
    )


@router.message(StateFilter(*QUESTION_STATES))
async def handle_wrong_input(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    key = await _current_question_key(state)
    await message.answer(TEXTS[lang]["need_button"])
    if key is not None:
        question = QUESTIONS[key]
        await message.answer(
            question["question"][lang],
            reply_markup=build_question_keyboard(key, question, lang),
        )
