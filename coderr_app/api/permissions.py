from rest_framework import permissions


class IsBusinessUser(permissions.BasePermission):
    """
    Returns if the given class is authenticated and is a business account when posting
    """
    message = "Only users with business profile may create offers."

    def has_permission(self, request, view):
        if request.method != "POST":
            return True
        u = request.user
        return bool(u and u.is_authenticated and hasattr(u, "profile") and u.profile.user_type == "business")


class IsCustomerUser(permissions.BasePermission):
    """
    Returns if the given class is authenticated and is a customer account when posting
    """
    message = "Only users with customer profile may perform this action."

    def has_permission(self, request, view):
        if request.method != "POST":
            return True
        u = request.user
        return bool(
            u and u.is_authenticated and hasattr(u, "profile") and getattr(u.profile, "user_type", None) == "customer")
