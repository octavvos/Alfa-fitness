"""Har bir Telegram chat uchun JWT sessiyasini xotirada saqlaydi.

Demo loyiha uchun oddiy in-memory lug'at yetarli. Ishlab chiqarishda buni
Redis yoki DBga ko'chirish tavsiya etiladi.
"""

SESSIONS: dict[int, dict] = {}


def save_session(telegram_id: int, *, access: str, refresh: str, role: str, full_name: str | None = None):
    SESSIONS[telegram_id] = {
        "access": access,
        "refresh": refresh,
        "role": role,
        "full_name": full_name,
    }


def get_session(telegram_id: int) -> dict | None:
    return SESSIONS.get(telegram_id)


def is_bound(telegram_id: int) -> bool:
    return telegram_id in SESSIONS
