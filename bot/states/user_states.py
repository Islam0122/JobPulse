from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    """Состояния для процесса онбординга пользователя"""
    waiting_for_role = State()  # Ожидание роли (Python Dev)
    waiting_for_level = State()  # Ожидание уровня (Junior/Middle)
    waiting_for_stack = State()  # Выбор технологий
    waiting_for_work_format = State()  # Remote/Office/Hybrid
    waiting_for_employment_type = State()  # Full-time/Part-time
    waiting_for_location = State()  # Город/страна
    waiting_for_salary = State()  # Зарплатные ожидания
    waiting_for_currency = State()  # Валюта (USD/EUR/RUB)
    waiting_for_notification_mode = State()  # Частота уведомлений
    profile_complete = State()  # Профиль заполнен