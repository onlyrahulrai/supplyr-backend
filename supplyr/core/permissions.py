from rest_framework import permissions

class IsUnapproved(permissions.IsAuthenticated):
    
    def has_permission(self, request, view):
        return super().has_permission(request, view) and not request.user.is_approved


class IsApproved(permissions.IsAuthenticated):
    
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_approved

class IsFromBuyerAPI(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        allowed = False
        if 'api_source' in view.kwargs and view.kwargs['api_source'] == 'buyer':
            allowed = True
            
        return super().has_permission(request, view) and allowed

class IsFromSellerAPI(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        allowed = False
        if 'api_source' in view.kwargs and view.kwargs['api_source'] == 'seller':
            allowed = True
            
        return super().has_permission(request, view) and allowed