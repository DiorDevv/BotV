"""Inline tugma klaviaturalarini quruvchi funksiyalar."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbek", callback_data="lang:uz")
    builder.button(text="🇷🇺 Русский", callback_data="lang:ru")
    builder.adjust(2)
    return builder.as_markup()


def build_question_keyboard(question_key: str, question: dict, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for option in question["options"]:
        builder.button(text=option[lang], callback_data=f"ans:{question_key}:{option['id']}")
    builder.adjust(1)
    return builder.as_markup()
