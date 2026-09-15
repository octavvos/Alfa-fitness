import io
import uuid
from datetime import date, datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from .. import api_client
from ..config import ADMIN_CONTACT_PHONE
from ..freeze_requests import add_request
from ..keyboards import client_menu, freeze_decision_keyboard
from ..session import SESSIONS, get_session
from ..states import FreezeStates

router = Router(name="client")


def _require_client_session(message: Message):
    session = get_session(message.from_user.id)
    if not session or session["role"] != "mijoz":
        return None
    return session


@router.message(F.text == "Mening abonementim")
async def my_membership(message: Message):
    session = _require_client_session(message)
    if not session:
        await message.answer("Avval /start bosib ro'yxatdan o'ting.")
        return

    try:
        data = await api_client.get_my_membership(session["access"])
    except api_client.ApiError:
        await message.answer(
            f"Sizda faol abonement yo'q yoki muddati tugagan.\n"
            f"Yangi abonement uchun administratorga murojaat qiling: {ADMIN_CONTACT_PHONE}"
        )
        return

    plan = data["plan"]
    text = (
        f"📋 Tarif: {plan['name']}\n"
        f"📅 Boshlanish: {data['start_date']}\n"
        f"📅 Tugash: {data['end_date']}\n"
        f"⏳ Qolgan kun: {data['left_days']}\n"
        f"🏋️ Ishlatilgan tashrif: {data['visits_used']}"
    )
    if data["left_visits"] is not None:
        text += f" (qolgan: {data['left_visits']})"
    text += f"\n❄️ Qolgan muzlatish kuni: {data['freeze_days_left']}"
    await message.answer(text, reply_markup=client_menu())


@router.message(F.text == "QR kod")
async def my_qr(message: Message):
    session = _require_client_session(message)
    if not session:
        await message.answer("Avval /start bosib ro'yxatdan o'ting.")
        return

    try:
        data = await api_client.get_my_membership(session["access"])
    except api_client.ApiError:
        await message.answer(
            f"Abonementingiz tugagan. Administrator telefoni: {ADMIN_CONTACT_PHONE}"
        )
        return

    import qrcode

    qr_img = qrcode.make(data["qr_token"])
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    await message.answer_photo(
        BufferedInputFile(buffer.read(), filename="qr.png"),
        caption="Zalga kirishda ushbu QR kodni administratorga ko'rsating.",
    )


@router.message(F.text == "Tashriflarim")
async def my_visits(message: Message):
    session = _require_client_session(message)
    if not session:
        await message.answer("Avval /start bosib ro'yxatdan o'ting.")
        return

    data = await api_client.get_my_visits(session["access"])
    results = data.get("results", data) if isinstance(data, dict) else data
    if not results:
        await message.answer("Hali tashriflar yo'q.")
        return

    lines = [f"• {v['checked_in_at']}" for v in results[:10]]
    await message.answer("So'nggi tashriflaringiz:\n" + "\n".join(lines))


@router.message(F.text == "Muzlatish so'rash")
async def freeze_start(message: Message, state: FSMContext):
    session = _require_client_session(message)
    if not session:
        await message.answer("Avval /start bosib ro'yxatdan o'ting.")
        return

    try:
        membership = await api_client.get_my_membership(session["access"])
    except api_client.ApiError:
        await message.answer("Sizda faol abonement yo'q, muzlatish so'rab bo'lmaydi.")
        return

    await state.update_data(membership_id=membership["id"], freeze_days_left=membership["freeze_days_left"])
    await message.answer(
        f"Qolgan muzlatish kuningiz: {membership['freeze_days_left']}.\n"
        "Muzlatish boshlanish sanasini kiriting (YYYY-MM-DD):"
    )
    await state.set_state(FreezeStates.waiting_start_date)


@router.message(FreezeStates.waiting_start_date)
async def freeze_start_date(message: Message, state: FSMContext):
    try:
        start_date = datetime.strptime(message.text.strip(), "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Sana formati noto'g'ri. Masalan: 2026-09-20")
        return
    if start_date < date.today():
        await message.answer("Boshlanish sanasi bugundan oldin bo'lishi mumkin emas.")
        return

    await state.update_data(start_date=start_date.isoformat())
    await message.answer("Necha kun muzlatmoqchisiz?")
    await state.set_state(FreezeStates.waiting_days)


@router.message(FreezeStates.waiting_days)
async def freeze_days(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, kunlar sonini raqamda kiriting.")
        return
    days = int(message.text.strip())
    data = await state.get_data()
    if days > data["freeze_days_left"]:
        await message.answer(
            f"Sizda faqat {data['freeze_days_left']} kun muzlatish huquqi qoldi. Kamroq son kiriting."
        )
        return

    await state.update_data(days=days)
    await message.answer("Muzlatish sababini yozing (masalan: kasallik, safar):")
    await state.set_state(FreezeStates.waiting_reason)


@router.message(FreezeStates.waiting_reason)
async def freeze_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    reason = message.text.strip()
    request_id = uuid.uuid4().hex[:12]

    add_request(
        request_id,
        membership_id=data["membership_id"],
        client_telegram_id=message.from_user.id,
        start_date=data["start_date"],
        days=data["days"],
        reason=reason,
    )

    admin_ids = [tid for tid, s in SESSIONS.items() if s["role"] == "admin"]
    if not admin_ids:
        await message.answer("Hozircha ulangan administrator yo'q. Iltimos, klubga murojaat qiling.")
    else:
        text = (
            "❄️ Yangi muzlatish so'rovi\n"
            f"Mijoz: {message.from_user.full_name}\n"
            f"Boshlanish: {data['start_date']}\n"
            f"Kunlar soni: {data['days']}\n"
            f"Sababi: {reason}"
        )
        for admin_id in admin_ids:
            await message.bot.send_message(admin_id, text, reply_markup=freeze_decision_keyboard(request_id))
        await message.answer("So'rovingiz administratorga yuborildi. Javobni kuting.")

    await state.clear()
    await message.answer("Bosh menyu:", reply_markup=client_menu())
