import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from memberships.models import AccessLog, Client, Membership, MembershipPlan, Visit

User = get_user_model()


class AccessCheckTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", phone="+998900000001", password="pass12345", role=User.Role.ADMIN
        )
        self.plan = MembershipPlan.objects.create(
            name="1 oy", duration_days=30, visit_limit=2, daily_limit=1, price=100000, freeze_days=5
        )
        self.client_user = User.objects.create_user(
            username="+998900000002", phone="+998900000002", password="pass12345", role=User.Role.CLIENT
        )
        self.client_profile = Client.objects.create(
            user=self.client_user, full_name="Test Mijoz", card_code="CARD0001"
        )
        self.client.force_authenticate(self.admin)
        self.today = timezone.localdate()

    def _check(self, token):
        url = reverse("access-check")
        return self.client.post(url, {"qr_token": str(token)}, format="json")

    def _membership(self, **overrides):
        defaults = dict(
            client=self.client_profile,
            plan=self.plan,
            start_date=self.today - timedelta(days=1),
            end_date=self.today + timedelta(days=29),
            price_paid=self.plan.price,
            status=Membership.Status.ACTIVE,
        )
        defaults.update(overrides)
        return Membership.objects.create(**defaults)

    def test_invalid_token_returns_not_found(self):
        response = self._check(uuid.uuid4())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["allowed"])
        self.assertEqual(response.data["reason"], "topilmadi")
        self.assertEqual(AccessLog.objects.last().result, AccessLog.Result.NOT_FOUND)

    def test_expired_membership_is_rejected(self):
        membership = self._membership(
            start_date=self.today - timedelta(days=60),
            end_date=self.today - timedelta(days=1),
            status=Membership.Status.EXPIRED,
        )
        response = self._check(membership.qr_token)
        self.assertFalse(response.data["allowed"])
        self.assertEqual(response.data["reason"], "muddati_tugagan")
        self.assertEqual(AccessLog.objects.last().result, AccessLog.Result.EXPIRED)

    def test_frozen_membership_is_rejected(self):
        membership = self._membership(status=Membership.Status.FROZEN)
        response = self._check(membership.qr_token)
        self.assertFalse(response.data["allowed"])
        self.assertEqual(response.data["reason"], "muzlatilgan")
        self.assertEqual(AccessLog.objects.last().result, AccessLog.Result.FROZEN)

    def test_daily_limit_reached_is_rejected(self):
        membership = self._membership()
        Visit.objects.create(membership=membership, checked_by=self.admin)
        response = self._check(membership.qr_token)
        self.assertFalse(response.data["allowed"])
        self.assertEqual(response.data["reason"], "kunlik_limit_tugagan")
        self.assertEqual(AccessLog.objects.last().result, AccessLog.Result.LIMIT_REACHED)

    def test_total_visit_limit_reached_is_rejected(self):
        membership = self._membership(visits_used=2)
        response = self._check(membership.qr_token)
        self.assertFalse(response.data["allowed"])
        self.assertEqual(response.data["reason"], "umumiy_limit_tugagan")
        self.assertEqual(AccessLog.objects.last().result, AccessLog.Result.LIMIT_REACHED)

    def test_allowed_access_creates_visit_and_increments_counter(self):
        membership = self._membership()
        response = self._check(membership.qr_token)
        self.assertTrue(response.data["allowed"])
        self.assertEqual(response.data["reason"], "ruxsat")
        membership.refresh_from_db()
        self.assertEqual(membership.visits_used, 1)
        self.assertEqual(Visit.objects.filter(membership=membership).count(), 1)
        self.assertEqual(AccessLog.objects.last().result, AccessLog.Result.ALLOWED)

    def test_double_scan_does_not_create_two_visits_same_day(self):
        membership = self._membership()
        first = self._check(membership.qr_token)
        second = self._check(membership.qr_token)
        self.assertTrue(first.data["allowed"])
        self.assertFalse(second.data["allowed"])
        self.assertEqual(second.data["reason"], "kunlik_limit_tugagan")
        self.assertEqual(Visit.objects.filter(membership=membership).count(), 1)


class MembershipFlowTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin2", phone="+998900000003", password="pass12345", role=User.Role.ADMIN
        )
        self.plan = MembershipPlan.objects.create(
            name="1 oy demo", duration_days=30, daily_limit=1, price=150000, freeze_days=5
        )
        self.client.force_authenticate(self.admin)

    def test_cannot_sell_second_active_membership(self):
        user = User.objects.create_user(
            username="+998900000004", phone="+998900000004", password="x", role=User.Role.CLIENT
        )
        client_profile = Client.objects.create(user=user, full_name="Ikkinchi Mijoz", card_code="CARD0002")
        url = reverse("membership-list")
        payload = {"client": client_profile.id, "plan": self.plan.id}
        first = self.client.post(url, payload, format="json")
        self.assertEqual(first.status_code, 201)
        second = self.client.post(url, payload, format="json")
        self.assertEqual(second.status_code, 400)
