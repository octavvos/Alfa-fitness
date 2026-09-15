import httpx

from .config import API_BASE_URL


class ApiError(Exception):
    def __init__(self, status_code: int, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API xato ({status_code}): {detail}")


def _auth_headers(access_token: str | None) -> dict:
    return {"Authorization": f"Bearer {access_token}"} if access_token else {}


async def _request(method: str, path: str, access_token: str | None = None, **kwargs):
    url = f"{API_BASE_URL}{path}"
    headers = _auth_headers(access_token)
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.request(method, url, headers=headers, **kwargs)
    if response.status_code >= 400:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise ApiError(response.status_code, detail)
    if response.status_code == 204:
        return None
    return response.json()


async def telegram_bind(phone: str, telegram_id: int) -> dict:
    return await _request("POST", "/auth/telegram-bind/", json={"phone": phone, "telegram_id": telegram_id})


async def get_my_membership(access_token: str) -> dict:
    return await _request("GET", "/memberships/my/", access_token=access_token)


async def get_my_visits(access_token: str) -> dict:
    return await _request("GET", "/visits/my/", access_token=access_token)


async def get_plans(access_token: str) -> dict:
    return await _request("GET", "/plans/?is_active=true", access_token=access_token)


async def request_freeze(access_token: str, membership_id: int, start_date: str, days: int, reason: str) -> dict:
    return await _request(
        "POST",
        f"/memberships/{membership_id}/freeze/",
        access_token=access_token,
        json={"start_date": start_date, "days": days, "reason": reason},
    )


async def check_access(access_token: str, qr_token: str) -> dict:
    return await _request("POST", "/access/check/", access_token=access_token, json={"qr_token": qr_token})
