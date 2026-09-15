from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from memberships.models import MembershipPlan

User = get_user_model()


class Command(BaseCommand):
    help = "Demo uchun admin foydalanuvchi va abonement turlarini yaratadi."

    def handle(self, *args, **options):
        if not User.objects.filter(role=User.Role.ADMIN).exists():
            User.objects.create_superuser(
                username="admin",
                phone="+998900000001",
                password="admin12345",
                role=User.Role.ADMIN,
            )
            self.stdout.write(self.style.SUCCESS("Admin yaratildi: admin / admin12345"))
        else:
            self.stdout.write("Admin allaqachon mavjud, o'tkazib yuborildi.")

        plans = [
            {"name": "1 oy — cheksiz", "duration_days": 30, "visit_limit": None, "daily_limit": 1, "price": 350000, "freeze_days": 7},
            {"name": "1 oy — 12 marta", "duration_days": 30, "visit_limit": 12, "daily_limit": 1, "price": 250000, "freeze_days": 5},
            {"name": "3 oy — cheksiz", "duration_days": 90, "visit_limit": None, "daily_limit": 2, "price": 900000, "freeze_days": 14},
        ]
        for plan_data in plans:
            plan, created = MembershipPlan.objects.get_or_create(name=plan_data["name"], defaults=plan_data)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Tarif yaratildi: {plan.name}"))

        self.stdout.write(self.style.SUCCESS("Demo ma'lumotlar tayyor."))
