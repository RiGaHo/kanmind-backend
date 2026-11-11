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
    queryset = Task.objects.select_related(
        "board", "assignee", "reviewer"
    ).prefetch_related("comments")
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, TaskPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ["list", "assigned_to_me", "reviewing"]:
            user = self.request.user
            return queryset.filter(
                Q(board__owner=user) | Q(board__members=user)
            ).distinct()
        return queryset

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=False, url_path="assigned-to-me")
    def assigned_to_me(self, request):
        tasks = self.get_queryset().filter(assignee=request.user)
        return Response(self.get_serializer(tasks, many=True).data)

    @action(detail=False)
    def reviewing(self, request):
        tasks = self.get_queryset().filter(reviewer=request.user)
        return Response(self.get_serializer(tasks, many=True).data)


class CommentScopeMixin:
    """Resolve and authorize the parent before selecting nested comments."""

    def get_task(self):
        task = get_object_or_404(
            Task.objects.select_related("board"), pk=self.kwargs["task_id"]
        )
        if not is_member(self.request.user, task.board):
            raise PermissionDenied("You are not a board member.")
        return task

    def get_queryset(self):
        return super().get_queryset().filter(task=self.get_task())


class CommentListView(CommentScopeMixin, generics.ListCreateAPIView):
    queryset = Comment.objects.select_related("author")
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(task=self.get_task(), author=self.request.user)


class CommentDetailView(CommentScopeMixin, generics.DestroyAPIView):
    queryset = Comment.objects.select_related("author")
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, CommentPermission]
