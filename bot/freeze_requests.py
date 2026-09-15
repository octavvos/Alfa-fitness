"""Mijozdan kelgan muzlatish so'rovlarini admin tasdiqlashini kutayotgan holda saqlaydi."""

PENDING_FREEZES: dict[str, dict] = {}


def add_request(request_id: str, **data):
    PENDING_FREEZES[request_id] = data


def pop_request(request_id: str) -> dict | None:
    return PENDING_FREEZES.pop(request_id, None)
