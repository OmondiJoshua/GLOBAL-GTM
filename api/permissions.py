from rest_framework import permissions

class IsAgent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'agent'

class IsSupervisor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'supervisor'

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'manager'

class AreaBasedPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'supervisor':
            return obj.area == request.user.area
        elif request.user.role == 'agent':
            return obj.assigned_to == request.user
        return True