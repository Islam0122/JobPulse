from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    """Состояния для процесса онбординга пользователя"""
    waiting_for_role = State()
    waiting_for_level = State()
    waiting_for_stack = State()
    waiting_for_work_format = State()
    waiting_for_employment_type = State()
    waiting_for_location = State()
    waiting_for_salary = State()
    waiting_for_currency = State()
    waiting_for_notification_mode = State()
    profile_complete = State()