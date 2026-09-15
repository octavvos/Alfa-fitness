from aiogram.fsm.state import State, StatesGroup


class FreezeStates(StatesGroup):
    waiting_start_date = State()
    waiting_days = State()
    waiting_reason = State()


class ScanStates(StatesGroup):
    scanning = State()
