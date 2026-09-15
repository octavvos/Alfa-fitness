from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from .. import api_client
from ..keyboards import admin_menu, client_menu, contact_keyboard, remove_keyboard
from ..session import get_session, save_session

router = Router(name="common")


@router.message(CommandStart())
async def cmd_start(message: Message):
    session = get_session(message.from_user.id)
    if session:
        menu = admin_menu() if session["role"] == "admin" else client_menu()
        await message.answer(
            f"Xush kelibsiz, {session.get('full_name') or message.from_user.full_name}!",
            reply_markup=menu,
        )
        return

    await message.answer(
        "Assalomu alaykum! Fitness klub botiga xush kelibsiz.\n"
        "Davom etish uchun telefon raqamingizni yuboring.",
        reply_markup=contact_keyboard(),
    )


@router.message(F.contact)
async def handle_contact(message: Message):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"

    try:
        data = await api_client.telegram_bind(phone, message.from_user.id)
    except api_client.ApiError:
        await message.answer(
            "Bu telefon raqami bo'yicha ro'yxatdan o'tilmagan. "
            "Administratorga murojaat qiling.",
            reply_markup=remove_keyboard(),
        )
        return

    save_session(
        message.from_user.id,
        access=data["access"],
        refresh=data["refresh"],
        role=data["role"],
        full_name=data.get("full_name"),
    )

    if data["role"] == "admin":
        await message.answer("Administrator sifatida ulandingiz.", reply_markup=admin_menu())
    else:
        await message.answer(
            f"Xush kelibsiz, {data.get('full_name', '')}! Akkauntingiz bog'landi.",
            reply_markup=client_menu(),
        )
