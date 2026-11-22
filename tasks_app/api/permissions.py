"""Task and comment object authorization."""

from rest_framework.permissions import BasePermission

from boards_app.api.permissions import is_member


class TaskPermission(BasePermission):
    """Require board access and restrict deletion to creator or owner."""

    def has_object_permission(self, request, view, obj):
        """Check board access before applying the task deletion rule."""
        if not is_member(request.user, obj.board):
            return False
        if request.method == "DELETE":
            return request.user.pk in [obj.creator_id, obj.board.owner_id]
        return True


class CommentPermission(BasePermission):
    """Restrict comment deletion to its author."""

    def has_object_permission(self, request, view, obj):
        """Allow deletion only when the requester authored the comment."""
        return request.method != "DELETE" or obj.author_id == request.user.pk
