from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    title = State()
    body = State()
    file = State()


