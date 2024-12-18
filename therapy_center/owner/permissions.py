from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    """
    مجوزی برای دسترسی فقط به کاربران با نقش 'owner'.
    """
    def has_permission(self, request, view):
        return request.user.role == 'owner'