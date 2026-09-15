import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class MembershipPlan(models.Model):
    name = models.CharField(max_length=100, unique=True)
    duration_days = models.PositiveSmallIntegerField()
    visit_limit = models.PositiveSmallIntegerField(null=True, blank=True)
    daily_limit = models.PositiveSmallIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    freeze_days = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Abonement turi"
        verbose_name_plural = "Abonement turlari"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Client(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client"
    )
    full_name = models.CharField(max_length=150)
    birth_date = models.DateField(null=True, blank=True)
    card_code = models.CharField(max_length=12, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.full_name} ({self.card_code})"


class Membership(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "faol", "Faol"
        FROZEN = "muzlatilgan", "Muzlatilgan"
        EXPIRED = "tugagan", "Tugagan"
        CANCELLED = "bekor", "Bekor qilingan"

    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="memberships")
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT, related_name="memberships")
    start_date = models.DateField()
    end_date = models.DateField(db_index=True)
    visits_used = models.PositiveSmallIntegerField(default=0)
    price_paid = models.DecimalField(max_digits=10, decimal_places=2)
    qr_token = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sold_memberships",
    )
    reminder_sent_at = models.DateField(
        null=True, blank=True, help_text="Oxirgi eslatma yuborilgan sana"
    )

    class Meta:
        verbose_name = "Sotilgan abonement"
        verbose_name_plural = "Sotilgan abonementlar"
        ordering = ("-id",)
        indexes = [models.Index(fields=["client", "status"])]
        constraints = [
            models.UniqueConstraint(
                fields=["client"],
                condition=Q(status="faol"),
                name="unique_active_membership_per_client",
            )
        ]

    def __str__(self):
        return f"{self.client} — {self.plan} ({self.status})"

    @property
    def left_days(self):
        from datetime import date

        delta = (self.end_date - date.today()).days
        return max(delta, 0)

    @property
    def left_visits(self):
        if self.plan.visit_limit is None:
            return None
        return max(self.plan.visit_limit - self.visits_used, 0)

    @property
    def freeze_days_used(self):
        return sum(f.days for f in self.freezes.all())

    @property
    def freeze_days_left(self):
        return max(self.plan.freeze_days - self.freeze_days_used, 0)


class Freeze(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="freezes")
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.PositiveSmallIntegerField()
    reason = models.CharField(max_length=255)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="approved_freezes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Muzlatish"
        verbose_name_plural = "Muzlatishlar"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.membership} — {self.days} kun"


class Visit(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.PROTECT, related_name="visits")
    checked_in_at = models.DateTimeField(auto_now_add=True, db_index=True)
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="checked_visits"
    )

    class Meta:
        verbose_name = "Tashrif"
        verbose_name_plural = "Tashriflar"
        ordering = ("-checked_in_at",)
        indexes = [models.Index(fields=["membership", "checked_in_at"])]

    def __str__(self):
        return f"{self.membership.client} — {self.checked_in_at:%Y-%m-%d %H:%M}"


class AccessLog(models.Model):
    class Result(models.TextChoices):
        ALLOWED = "ruxsat", "Ruxsat"
        EXPIRED = "muddati_tugagan", "Muddati tugagan"
        FROZEN = "muzlatilgan", "Muzlatilgan"
        LIMIT_REACHED = "limit_tugagan", "Limit tugagan"
        NOT_FOUND = "topilmadi", "Topilmadi"

    qr_token = models.CharField(max_length=64)
    membership = models.ForeignKey(
        Membership, on_delete=models.SET_NULL, null=True, related_name="access_logs"
    )
    result = models.CharField(max_length=30, choices=Result.choices)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Kirish urinishi"
        verbose_name_plural = "Kirish urinishlari"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.qr_token[:8]}… — {self.result}"
