from rest_framework import permissions

class IsUnapproved(permissions.IsAuthenticated):
    
    def has_permission(self, request, view):
        return super().has_permission(request, view) and not request.user.is_approved


class IsApproved(permissions.IsAuthenticated):
    
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_approved