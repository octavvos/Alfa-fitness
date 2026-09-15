import django_filters as filters

from memberships.models import AccessLog, Membership, MembershipPlan, Visit


class MembershipPlanFilter(filters.FilterSet):
    class Meta:
        model = MembershipPlan
        fields = ["is_active"]


class MembershipFilter(filters.FilterSet):
    end_date_from = filters.DateFilter(field_name="end_date", lookup_expr="gte")
    end_date_to = filters.DateFilter(field_name="end_date", lookup_expr="lte")

    class Meta:
        model = Membership
        fields = ["status", "plan", "end_date_from", "end_date_to"]


class VisitFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="checked_in_at", lookup_expr="date__gte")
    date_to = filters.DateFilter(field_name="checked_in_at", lookup_expr="date__lte")
    client = filters.NumberFilter(field_name="membership__client_id")

    class Meta:
        model = Visit
        fields = ["date_from", "date_to", "client"]


class AccessLogFilter(filters.FilterSet):
    class Meta:
        model = AccessLog
        fields = ["result"]
