from rest_framework import permissions

class IsUnapproved(permissions.IsAuthenticated):
    
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.status != 'approved'