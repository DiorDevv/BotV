"""/start buyrug'i va til tanlash bosqichi."""
import logging

from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from criteria import QUESTIONS
from keyboards import build_language_keyboard, build_question_keyboard
from states import Form
from texts import CHOOSE_LANGUAGE_TEXT, TEXTS

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(
        tg_id=message.from_user.id,
        tg_username=message.from_user.username,
    )
    await state.set_state(Form.language)
    await message.answer(CHOOSE_LANGUAGE_TEXT, reply_markup=build_language_keyboard())


@router.callback_query(StateFilter(Form.language), F.data.startswith("lang:"))
async def handle_language_choice(callback: CallbackQuery, state: FSMContext) -> None:
    lang = callback.data.split(":", 1)[1]
    if lang not in ("uz", "ru"):
        await callback.answer()
        return

    await state.update_data(lang=lang)
    await callback.answer()

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback.message.answer(TEXTS[lang]["welcome"])

    first_key = "age"
    question = QUESTIONS[first_key]
    await state.set_state(question["state"])
    await callback.message.answer(
        question["question"][lang],
        reply_markup=build_question_keyboard(first_key, question, lang),
    )


@router.message(StateFilter(Form.language))
async def handle_language_wrong_input(message: Message) -> None:
    await message.answer(CHOOSE_LANGUAGE_TEXT, reply_markup=build_language_keyboard())


@router.message(StateFilter(None))
async def handle_no_active_conversation(message: Message) -> None:
    await message.answer(f"{TEXTS['uz']['please_start']}\n{TEXTS['ru']['please_start']}")
