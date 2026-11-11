"""Board CRUD with visibility filtering and object authorization."""

from django.db.models import Q
from rest_framework import permissions, viewsets

from boards_app.models import Board

from .permissions import BoardPermission
from .serializers import BoardSerializer


class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.prefetch_related("members", "tasks").all()
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated, BoardPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            user = self.request.user
            return queryset.filter(Q(owner=user) | Q(members=user)).distinct()
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
