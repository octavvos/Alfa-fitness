from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register("plans", views.MembershipPlanViewSet, basename="plan")
router.register("clients", views.ClientViewSet, basename="client")
router.register("memberships", views.MembershipViewSet, basename="membership")
router.register("visits", views.VisitViewSet, basename="visit")
router.register("access-logs", views.AccessLogViewSet, basename="access-log")

urlpatterns = [
    path("auth/login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/telegram-bind/", views.TelegramBindView.as_view(), name="auth-telegram-bind"),
    path("auth/me/", views.MeView.as_view(), name="auth-me"),
    path("access/check/", views.AccessCheckView.as_view(), name="access-check"),
    path("reports/expiring/", views.ExpiringReportView.as_view(), name="report-expiring"),
    path("reports/daily/", views.DailyReportView.as_view(), name="report-daily"),
    path("reports/attendance/", views.AttendanceReportView.as_view(), name="report-attendance"),
]
urlpatterns += router.urls
