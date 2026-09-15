from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "phone", "role", "telegram_id", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "phone", "first_name", "last_name")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Fitness klub", {"fields": ("role", "phone", "telegram_id")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Fitness klub", {"fields": ("role", "phone", "telegram_id")}),
    )
