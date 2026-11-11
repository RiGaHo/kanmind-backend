"""Task and comment object authorization."""

from rest_framework.permissions import BasePermission

from boards_app.api.permissions import is_member


class TaskPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not is_member(request.user, obj.board):
            return False
        if request.method == "DELETE":
            return request.user.pk in [obj.creator_id, obj.board.owner_id]
        return True


class CommentPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method != "DELETE" or obj.author_id == request.user.pk
