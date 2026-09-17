"""FSM states for the candidate conversation flow."""
from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    language = State()
    age = State()
    education_direction = State()
    degree = State()
    course = State()
    education_form = State()
    waiting_for_cv = State()
