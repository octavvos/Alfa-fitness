import logging

import httpx
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from memberships.models import Membership, MembershipPlan

logger = logging.getLogger(__name__)


def _send_telegram_message(telegram_id: int, text: str):
    if not settings.BOT_TOKEN:
        logger.warning("BOT_TOKEN sozlanmagan, xabar yuborilmadi.")
        return
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
    try:
        httpx.post(url, json={"chat_id": telegram_id, "text": text}, timeout=10)
    except httpx.HTTPError:
        logger.exception("Telegram xabarini yuborishda xatolik (chat_id=%s)", telegram_id)


@shared_task
def expire_memberships():
    """Muddati tugagan faol abonementlarni 'tugagan' statusiga o'tkazadi."""
    today = timezone.localdate()
    updated = Membership.objects.filter(
        status=Membership.Status.ACTIVE, end_date__lt=today
    ).update(status=Membership.Status.EXPIRED)
    logger.info("expire_memberships: %s ta abonement yopildi", updated)
    return updated


@shared_task
def unfreeze_memberships():
    """Muzlatish davri tugagan abonementlarni yana 'faol' statusiga qaytaradi."""
    today = timezone.localdate()
    count = 0
    frozen = Membership.objects.filter(status=Membership.Status.FROZEN).prefetch_related("freezes")
    for membership in frozen:
        last_freeze = membership.freezes.order_by("-end_date").first()
        if last_freeze and last_freeze.end_date <= today:
            membership.status = Membership.Status.ACTIVE
            membership.save(update_fields=["status"])
            count += 1
    logger.info("unfreeze_memberships: %s ta abonement faollashtirildi", count)
    return count


@shared_task
def send_expiry_reminders():
    """Kuniga bir marta: 3 kundan kam qolganlarga eslatma, bugun tugaganlarga yangilash taklifi."""
    today = timezone.localdate()
    qs = (
        Membership.objects.filter(status=Membership.Status.ACTIVE)
        .exclude(reminder_sent_at=today)
        .exclude(client__user__telegram_id__isnull=True)
        .select_related("client__user", "plan")
    )
    sent = 0
    active_plans = None
    for membership in qs:
        days_left = (membership.end_date - today).days
        if days_left < 0 or days_left > 2:
            continue

        if days_left == 0:
            if active_plans is None:
                active_plans = list(MembershipPlan.objects.filter(is_active=True))
            plans_text = "\n".join(f"• {p.name} — {p.price} so'm" for p in active_plans)
            text = (
                f"Hurmatli {membership.client.full_name}, abonementingiz bugun tugadi.\n"
                f"Yangilash uchun quyidagi tariflardan birini tanlashingiz mumkin:\n{plans_text}"
            )
        else:
            text = (
                f"Hurmatli {membership.client.full_name}, abonementingiz muddati "
                f"{days_left} kundan keyin tugaydi."
            )

        _send_telegram_message(membership.client.user.telegram_id, text)
        membership.reminder_sent_at = today
        membership.save(update_fields=["reminder_sent_at"])
        sent += 1

    logger.info("send_expiry_reminders: %s ta eslatma yuborildi", sent)
    return sent
