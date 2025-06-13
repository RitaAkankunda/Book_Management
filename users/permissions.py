from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Permission check for admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'ADMIN'

class IsModerator(permissions.BasePermission):
    """
    Permission check for moderator users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role in ['ADMIN', 'MODERATOR']

class IsUser(permissions.BasePermission):
    """
    Permission check for regular users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role in ['ADMIN', 'MODERATOR', 'USER']
