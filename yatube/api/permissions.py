from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Класс разрешения, где изменять и удалять объект может только владелец,
    остальные могут только просматривать."""
    message = "You're not an owner to change it!"

    def has_object_permission(self, request, view, obj):
        return (obj.author == request.user) or (request.method in SAFE_METHODS)
