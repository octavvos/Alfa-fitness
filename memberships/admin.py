from django.contrib import admin

from .models import AccessLog, Client, Freeze, Membership, MembershipPlan, Visit


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_days", "visit_limit", "daily_limit", "price", "freeze_days", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "card_code", "phone", "created_at")
    search_fields = ("full_name", "card_code", "user__phone")
    list_filter = ("created_at",)

    @admin.display(description="Telefon")
    def phone(self, obj):
        return obj.user.phone


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("client", "plan", "start_date", "end_date", "status", "visits_used", "price_paid")
    list_filter = ("status", "plan")
    search_fields = ("client__full_name", "client__card_code", "qr_token")
    date_hierarchy = "end_date"


@admin.register(Freeze)
class FreezeAdmin(admin.ModelAdmin):
    list_display = ("membership", "start_date", "end_date", "days", "approved_by")
    list_filter = ("start_date",)
    search_fields = ("membership__client__full_name",)


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("membership", "checked_in_at", "checked_by")
    list_filter = ("checked_in_at",)
    search_fields = ("membership__client__full_name",)


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ("qr_token", "membership", "result", "created_at")
    list_filter = ("result", "created_at")
    search_fields = ("qr_token",)
