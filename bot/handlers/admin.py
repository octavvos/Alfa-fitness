import io

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .. import api_client
from ..keyboards import admin_menu, client_menu
from ..session import get_session
from ..states import ScanStates
from ..freeze_requests import pop_request

router = Router(name="admin")


def _require_admin_session(message: Message):
    session = get_session(message.from_user.id)
    if not session or session["role"] != "admin":
        return None
    return session


def _decode_qr_from_bytes(image_bytes: bytes) -> str | None:
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode
    except ImportError:
        return None

    image = Image.open(io.BytesIO(image_bytes))
    results = decode(image)
    if not results:
        return None
    return results[0].data.decode("utf-8")


@router.message(F.text == "Skanerlash")
async def start_scanning(message: Message, state: FSMContext):
    session = _require_admin_session(message)
    if not session:
        await message.answer("Bu bo'lim faqat administratorlar uchun.")
        return
    await state.set_state(ScanStates.scanning)
    await message.answer(
        "Skanerlash rejimi yoqildi. Mijozning QR kod rasmini yuboring yoki tokenni matn sifatida kiriting."
    )


@router.message(F.text == "Skanerlashni to'xtatish")
async def stop_scanning(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Skanerlash rejimi o'chirildi.", reply_markup=admin_menu())


@router.message(ScanStates.scanning, F.photo)
async def scan_photo(message: Message, state: FSMContext):
    session = _require_admin_session(message)
    if not session:
        await message.answer("Bu bo'lim faqat administratorlar uchun.")
        return
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    buffer = await message.bot.download_file(file.file_path)
    token = _decode_qr_from_bytes(buffer.read())

    if not token:
        await message.answer(
            "QR kodni o'qib bo'lmadi. Iltimos, tokenni matn sifatida yuboring yoki aniqroq rasm oling."
        )
        return

    await _run_access_check(message, session, token)


@router.message(ScanStates.scanning, F.text)
async def scan_text(message: Message, state: FSMContext):
    session = _require_admin_session(message)
    if not session:
        await message.answer("Bu bo'lim faqat administratorlar uchun.")
        return
    await _run_access_check(message, session, message.text.strip())


async def _run_access_check(message: Message, session: dict, token: str):
    try:
        result = await api_client.check_access(session["access"], token)
    except api_client.ApiError as exc:
        await message.answer(f"Xatolik: {exc.detail}")
        return

    reason_labels = {
        "ruxsat": "Ruxsat berildi",
        "topilmadi": "Token topilmadi",
        "muddati_tugagan": "Abonement muddati tugagan",
        "muzlatilgan": "Abonement muzlatilgan",
        "kunlik_limit_tugagan": "Kunlik limitga yetgan",
        "umumiy_limit_tugagan": "Umumiy limitga yetgan",
    }
    label = reason_labels.get(result["reason"], result["reason"])

    if result["allowed"]:
        client = result["client"]
        text = (
            f"✅ {label}\n"
            f"F.I.SH: {client['full_name']}\n"
            f"Tarif: {client['plan']}\n"
            f"Qolgan kun: {result['left_days']}\n"
            f"Bugungi tashrif: {result.get('today_visits', '-')}"
        )
    else:
        text = f"⛔ {label}"
        if result.get("client"):
            text += f"\nF.I.SH: {result['client']['full_name']}"

    await message.answer(text)


@router.callback_query(F.data.startswith("freeze_approve:"))
async def approve_freeze(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    if not session or session["role"] != "admin":
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return

    request_id = callback.data.split(":", 1)[1]
    data = pop_request(request_id)
    if not data:
        await callback.answer("So'rov muddati o'tgan.", show_alert=True)
        return

    try:
        await api_client.request_freeze(
            session["access"], data["membership_id"], data["start_date"], data["days"], data["reason"]
        )
    except api_client.ApiError as exc:
        await callback.message.edit_text(f"Xatolik: {exc.detail}")
        await callback.answer()
        return

    await callback.message.edit_text(callback.message.text + "\n\n✅ Tasdiqlandi.")
    await callback.bot.send_message(
        data["client_telegram_id"],
        f"Muzlatish so'rovingiz tasdiqlandi. {data['days']} kunga abonementingiz muzlatildi.",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("freeze_reject:"))
async def reject_freeze(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    if not session or session["role"] != "admin":
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return

    request_id = callback.data.split(":", 1)[1]
    data = pop_request(request_id)
    if not data:
        await callback.answer("So'rov muddati o'tgan.", show_alert=True)
        return

    await callback.message.edit_text(callback.message.text + "\n\n❌ Rad etildi.")
    await callback.bot.send_message(
        data["client_telegram_id"], "Afsuski, muzlatish so'rovingiz rad etildi."
    )
    await callback.answer()
