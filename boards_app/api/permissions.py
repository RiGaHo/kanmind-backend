"""Board access policy."""

from rest_framework.permissions import BasePermission


def is_member(user, board):
    return board.owner_id == user.pk or board.members.filter(pk=user.pk).exists()


class BoardPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE":
            return obj.owner_id == request.user.pk
        return is_member(request.user, obj)
