from datetime import timedelta

from django.db import transaction
from django.db.models import Count, F, Sum
from django.db.models.functions import ExtractHour, ExtractWeekDay
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from memberships.models import AccessLog, Client, Freeze, Membership, MembershipPlan, Visit

from .filters import AccessLogFilter, MembershipFilter, MembershipPlanFilter, VisitFilter
from .permissions import IsAdmin, IsAdminOrReadOnly, IsClient
from .serializers import (
    AccessCheckSerializer,
    AccessLogSerializer,
    ClientCreateSerializer,
    ClientSerializer,
    FreezeCreateSerializer,
    FreezeSerializer,
    MembershipCreateSerializer,
    MembershipPlanSerializer,
    MembershipSerializer,
    TelegramBindSerializer,
    UserMiniSerializer,
    VisitSerializer,
)


class MeView(APIView):
    """Joriy foydalanuvchi profili — SPA login qilgach rolini aniqlash uchun."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserMiniSerializer(request.user).data)


class TelegramBindView(APIView):
    """Bot foydalanuvchisi telefon raqami orqali o'z akkauntiga ulanadi va JWT oladi."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TelegramBindSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        telegram_id = serializer.validated_data["telegram_id"]

        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(phone=phone)
        user.telegram_id = telegram_id
        user.save(update_fields=["telegram_id"])

        refresh = RefreshToken.for_user(user)
        data = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": user.role,
        }
        if hasattr(user, "client"):
            data["full_name"] = user.client.full_name
        return Response(data)


class MembershipPlanViewSet(viewsets.ModelViewSet):
    queryset = MembershipPlan.objects.all()
    serializer_class = MembershipPlanSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = MembershipPlanFilter


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.select_related("user").all()
    permission_classes = [IsAdmin]
    search_fields = ["full_name", "user__phone", "card_code"]

    def get_serializer_class(self):
        if self.action == "create":
            return ClientCreateSerializer
        return ClientSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client = serializer.save()
        data = ClientSerializer(client).data
        data["generated_password"] = getattr(client, "generated_password", None)
        return Response(data, status=status.HTTP_201_CREATED)


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.select_related("client", "client__user", "plan", "created_by").all()
    permission_classes = [IsAdmin]
    filterset_class = MembershipFilter
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return MembershipCreateSerializer
        return MembershipSerializer

    def get_permissions(self):
        if self.action == "my":
            return [IsClient()]
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="my")
    def my(self, request):
        try:
            client = request.user.client
        except Client.DoesNotExist:
            return Response({"detail": "Mijoz profili topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        membership = (
            Membership.objects.filter(client=client, status=Membership.Status.ACTIVE)
            .select_related("plan", "client")
            .first()
        )
        if not membership:
            return Response({"detail": "Faol abonement topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        return Response(MembershipSerializer(membership).data)

    @action(detail=True, methods=["post"], url_path="freeze")
    def freeze(self, request, pk=None):
        membership = self.get_object()
        if membership.status != Membership.Status.ACTIVE:
            return Response(
                {"detail": "Faqat faol abonementni muzlatish mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = FreezeCreateSerializer(data=request.data, context={"membership": membership})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            freeze = Freeze.objects.create(
                membership=membership,
                start_date=data["start_date"],
                end_date=data["end_date"],
                days=data["days"],
                reason=data["reason"],
                approved_by=request.user,
            )
            membership.end_date = membership.end_date + timedelta(days=data["days"])
            membership.status = Membership.Status.FROZEN
            membership.save(update_fields=["end_date", "status"])

        return Response(
            {
                "freeze": FreezeSerializer(freeze).data,
                "membership": MembershipSerializer(membership).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        membership = self.get_object()
        membership.status = Membership.Status.CANCELLED
        membership.save(update_fields=["status"])
        return Response(MembershipSerializer(membership).data)


class AccessCheckView(APIView):
    """QR token bo'yicha kirishni tekshiradi: ketma-ket shartlar, aniq sabab, AccessLog har doim yoziladi."""

    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = AccessCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["qr_token"]
        today = timezone.localdate()

        with transaction.atomic():
            membership = (
                Membership.objects.select_for_update()
                .select_related("client", "client__user", "plan")
                .filter(qr_token=token)
                .first()
            )

            if membership is None:
                self._log(token, None, AccessLog.Result.NOT_FOUND)
                return self._response(False, "topilmadi")

            if membership.status == Membership.Status.FROZEN:
                self._log(token, membership, AccessLog.Result.FROZEN)
                return self._response(False, "muzlatilgan", membership)

            if membership.status in (Membership.Status.EXPIRED, Membership.Status.CANCELLED) or not (
                membership.start_date <= today <= membership.end_date
            ):
                self._log(token, membership, AccessLog.Result.EXPIRED)
                return self._response(False, "muddati_tugagan", membership)

            today_visits = membership.visits.filter(checked_in_at__date=today).count()
            if today_visits >= membership.plan.daily_limit:
                self._log(token, membership, AccessLog.Result.LIMIT_REACHED)
                return self._response(False, "kunlik_limit_tugagan", membership)

            if membership.plan.visit_limit is not None and membership.visits_used >= membership.plan.visit_limit:
                self._log(token, membership, AccessLog.Result.LIMIT_REACHED)
                return self._response(False, "umumiy_limit_tugagan", membership)

            Visit.objects.create(membership=membership, checked_by=request.user)
            Membership.objects.filter(pk=membership.pk).update(visits_used=F("visits_used") + 1)
            membership.refresh_from_db()
            self._log(token, membership, AccessLog.Result.ALLOWED)
            return self._response(True, "ruxsat", membership, today_visits=today_visits + 1)

    @staticmethod
    def _log(token, membership, result):
        AccessLog.objects.create(qr_token=str(token), membership=membership, result=result)

    @staticmethod
    def _response(allowed, reason, membership=None, today_visits=None):
        payload = {"allowed": allowed, "reason": reason, "client": None, "left_days": None}
        if membership is not None:
            payload["client"] = {
                "full_name": membership.client.full_name,
                "card_code": membership.client.card_code,
                "plan": membership.plan.name,
            }
            payload["left_days"] = membership.left_days
        if today_visits is not None:
            payload["today_visits"] = today_visits
        return Response(payload)


class VisitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Visit.objects.select_related("membership", "membership__client").all()
    serializer_class = VisitSerializer
    permission_classes = [IsAdmin]
    filterset_class = VisitFilter

    def get_permissions(self):
        if self.action == "my":
            return [IsClient()]
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="my")
    def my(self, request):
        try:
            client = request.user.client
        except Client.DoesNotExist:
            return Response({"detail": "Mijoz profili topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        visits = self.get_queryset().filter(membership__client=client)
        page = self.paginate_queryset(visits)
        serializer = self.get_serializer(page or visits, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class AccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AccessLog.objects.select_related("membership", "membership__client").all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAdmin]
    filterset_class = AccessLogFilter


class ExpiringReportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 7))
        today = timezone.localdate()
        memberships = Membership.objects.filter(
            status=Membership.Status.ACTIVE,
            end_date__gte=today,
            end_date__lte=today + timedelta(days=days),
        ).select_related("client", "plan")
        return Response(MembershipSerializer(memberships, many=True).data)


class DailyReportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        target_date = request.query_params.get("date")
        today = timezone.localdate()
        if target_date:
            from datetime import date

            target_date = date.fromisoformat(target_date)
        else:
            target_date = today

        visits_count = Visit.objects.filter(checked_in_at__date=target_date).count()
        todays_sales = Membership.objects.filter(start_date=target_date)
        sales_sum = todays_sales.aggregate(total=Sum("price_paid"))["total"] or 0
        new_memberships = todays_sales.count()
        return Response(
            {
                "date": target_date,
                "visits_count": visits_count,
                "new_memberships": new_memberships,
                "sales_sum": sales_sum,
            }
        )


class AttendanceReportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.localdate()
        week_ago = today - timedelta(days=7)
        qs = (
            Visit.objects.filter(checked_in_at__date__gte=week_ago)
            .annotate(hour=ExtractHour("checked_in_at"), weekday=ExtractWeekDay("checked_in_at"))
            .values("weekday", "hour")
            .annotate(total=Count("id"))
            .order_by("weekday", "hour")
        )
        return Response(list(qs))
