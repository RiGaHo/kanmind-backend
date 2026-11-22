"""Task CRUD, personal dashboard lists, and nested comments."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from boards_app.api.permissions import is_member
from tasks_app.models import Comment, Task

from .permissions import CommentPermission, TaskPermission
from .serializers import CommentSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """Expose authorized task operations and personal assignment lists."""

    queryset = Task.objects.select_related(
        "board", "assignee", "reviewer"
    ).prefetch_related("comments")
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, TaskPermission]

    def get_queryset(self):
        """Limit task lists to boards accessible to the current user."""
        queryset = super().get_queryset()
        if self.action in ["list", "assigned_to_me", "reviewing"]:
            user = self.request.user
            return queryset.filter(
                Q(board__owner=user) | Q(board__members=user)
            ).distinct()
        return queryset

    def perform_create(self, serializer):
        """Record the authenticated user as the task creator."""
        serializer.save(creator=self.request.user)

    @action(detail=False, url_path="assigned-to-me")
    def assigned_to_me(self, request):
        """Return accessible tasks assigned to the current user."""
        tasks = self.get_queryset().filter(assignee=request.user)
        return Response(self.get_serializer(tasks, many=True).data)

    @action(detail=False)
    def reviewing(self, request):
        """Return accessible tasks awaiting the current user as reviewer."""
        tasks = self.get_queryset().filter(reviewer=request.user)
        return Response(self.get_serializer(tasks, many=True).data)


class CommentScopeMixin:
    """Resolve and authorize the parent before selecting nested comments."""

    def get_task(self):
        """Resolve the parent task and require access to its board."""
        task = get_object_or_404(
            Task.objects.select_related("board"), pk=self.kwargs["task_id"]
        )
        if not is_member(self.request.user, task.board):
            raise PermissionDenied("You are not a board member.")
        return task

    def get_queryset(self):
        """Restrict comment selection to the authorized parent task."""
        return super().get_queryset().filter(task=self.get_task())


class CommentListView(CommentScopeMixin, generics.ListCreateAPIView):
    """List and create comments within an authorized task."""

    queryset = Comment.objects.select_related("author")
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Bind new comments to the authorized task and current author."""
        serializer.save(task=self.get_task(), author=self.request.user)


class CommentDetailView(CommentScopeMixin, generics.DestroyAPIView):
    """Delete an authored comment within its authorized parent task."""

    queryset = Comment.objects.select_related("author")
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, CommentPermission]
