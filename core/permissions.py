from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение на уровне объекта, позволяющее редактировать объект только его владельцам
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


class IsDocumentOwner(permissions.BasePermission):
    """
    Разрешение, позволяющее доступ к документу только его владельцам
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsOrderOwner(permissions.BasePermission):
    """
    Разрешение, позволяющее доступ к заказу только его владельцам
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user