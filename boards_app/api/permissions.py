"""Board access policy."""

from rest_framework.permissions import BasePermission


def is_member(user, board):
    """Treat board owners and explicit members as having board access."""
    return board.owner_id == user.pk or board.members.filter(pk=user.pk).exists()


class BoardPermission(BasePermission):
    """Allow member access while reserving deletion for the board owner."""

    def has_object_permission(self, request, view, obj):
        """Check ownership for deletion and board access for other operations."""
        if request.method == "DELETE":
            return obj.owner_id == request.user.pk
        return is_member(request.user, obj)
