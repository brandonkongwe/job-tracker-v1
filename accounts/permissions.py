from rest_framework.permissions import BasePermission, IsAuthenticated  # noqa: F401


class IsAdminRole(BasePermission):
    """
    Grants access only to users with role=Admin.
    Different from DRF's IsAdminUser (which checks is_staff).
    Use this for business-logic admin gating; use IsAdminUser for
    Django admin / management access.
    """

    message = "Access restricted to administrators."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_admin
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission.
    Allows access if the requesting user owns the object (obj.user == request.user)
    or is an admin.

    The view must call self.get_object() to trigger this check.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        # Support objects with either .user or .owner FK to User
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return owner == request.user


class IsOwner(BasePermission):
    """
    Object-level permission — only the owner of an object may access it.
    No admin bypass. Useful for truly private data (e.g., CV files).
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return owner == request.user