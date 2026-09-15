from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdmin(BasePermission):
    """Faqat role='admin' bo'lgan foydalanuvchilar uchun ruxsat."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_admin_role
        )


class IsClient(BasePermission):
    """Faqat role='mijoz' bo'lgan foydalanuvchilar uchun ruxsat."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_client_role
        )


class IsAdminOrReadOnly(BasePermission):
    """Hammasi o'qiy oladi, faqat admin o'zgartira oladi."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_admin_role
