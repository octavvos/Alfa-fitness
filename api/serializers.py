from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import serializers

from memberships.models import AccessLog, Client, Freeze, Membership, MembershipPlan, Visit

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "phone", "role")


class MembershipPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPlan
        fields = (
            "id", "name", "duration_days", "visit_limit", "daily_limit",
            "price", "freeze_days", "is_active",
        )


class ClientSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="user.phone", read_only=True)
    telegram_id = serializers.IntegerField(source="user.telegram_id", read_only=True)

    class Meta:
        model = Client
        fields = ("id", "full_name", "birth_date", "card_code", "phone", "telegram_id", "created_at")
        read_only_fields = ("created_at",)


class ClientCreateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True)

    class Meta:
        model = Client
        fields = ("id", "full_name", "birth_date", "card_code", "phone")

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Bu telefon raqami bilan foydalanuvchi allaqachon mavjud.")
        return value

    def create(self, validated_data):
        phone = validated_data.pop("phone")
        raw_password = get_random_string(10)
        user = User.objects.create(
            username=phone,
            phone=phone,
            role=User.Role.CLIENT,
            password=make_password(raw_password),
        )
        client = Client.objects.create(user=user, **validated_data)
        client.generated_password = raw_password
        return client


class MembershipSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    plan = MembershipPlanSerializer(read_only=True)
    created_by = UserMiniSerializer(read_only=True)
    left_days = serializers.IntegerField(read_only=True)
    left_visits = serializers.SerializerMethodField()
    freeze_days_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Membership
        fields = (
            "id", "client", "plan", "start_date", "end_date", "visits_used",
            "price_paid", "qr_token", "status", "created_by", "left_days", "left_visits",
            "freeze_days_left",
        )
        read_only_fields = fields

    def get_left_visits(self, obj):
        return obj.left_visits


class MembershipCreateSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(required=False)

    class Meta:
        model = Membership
        fields = ("id", "client", "plan", "start_date")

    def validate(self, attrs):
        client = attrs["client"]
        if Membership.objects.filter(client=client, status=Membership.Status.ACTIVE).exists():
            raise serializers.ValidationError(
                "Bu mijozda allaqachon faol abonement mavjud. Avval uni tugatish yoki bekor qilish kerak."
            )
        return attrs

    def create(self, validated_data):
        plan = validated_data["plan"]
        start_date = validated_data.get("start_date") or timezone.localdate()
        membership = Membership.objects.create(
            client=validated_data["client"],
            plan=plan,
            start_date=start_date,
            end_date=start_date + timedelta(days=plan.duration_days),
            price_paid=plan.price,
            created_by=self.context["request"].user,
        )
        return membership

    def to_representation(self, instance):
        return MembershipSerializer(instance, context=self.context).data


class FreezeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Freeze
        fields = ("id", "membership", "start_date", "end_date", "days", "reason", "approved_by", "created_at")
        read_only_fields = ("id", "membership", "end_date", "approved_by", "created_at")


class FreezeCreateSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    days = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=255)

    def validate(self, attrs):
        membership: Membership = self.context["membership"]
        used_days = sum(f.days for f in membership.freezes.all())
        if used_days + attrs["days"] > membership.plan.freeze_days:
            remaining = max(membership.plan.freeze_days - used_days, 0)
            raise serializers.ValidationError(
                f"Muzlatish kunlari yetarli emas. Qolgan muzlatish kuni: {remaining}."
            )
        new_start = attrs["start_date"]
        new_end = new_start + timedelta(days=attrs["days"])
        for freeze in membership.freezes.all():
            if new_start < freeze.end_date and freeze.start_date < new_end:
                raise serializers.ValidationError(
                    "Bu davr boshqa muzlatish davri bilan kesishadi."
                )
        attrs["end_date"] = new_end
        return attrs


class VisitSerializer(serializers.ModelSerializer):
    client = serializers.CharField(source="membership.client.full_name", read_only=True)

    class Meta:
        model = Visit
        fields = ("id", "membership", "client", "checked_in_at", "checked_by")
        read_only_fields = fields


class AccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessLog
        fields = ("id", "qr_token", "membership", "result", "created_at")
        read_only_fields = fields


class AccessCheckSerializer(serializers.Serializer):
    qr_token = serializers.CharField(max_length=64)


class TelegramBindSerializer(serializers.Serializer):
    phone = serializers.CharField()
    telegram_id = serializers.IntegerField()

    def validate_phone(self, value):
        if not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Bu raqam bilan foydalanuvchi topilmadi.")
        return value
