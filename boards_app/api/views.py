"""Board CRUD with visibility filtering and object authorization."""

from django.db.models import Q
from rest_framework import permissions, viewsets

from boards_app.models import Board

from .permissions import BoardPermission
from .serializers import BoardSerializer


class BoardViewSet(viewsets.ModelViewSet):
    """Expose board operations with membership and ownership checks."""

    queryset = Board.objects.prefetch_related("members", "tasks").all()
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated, BoardPermission]

    def get_queryset(self):
        """Limit board lists to owned or joined boards."""
        queryset = super().get_queryset()
        if self.action == "list":
            user = self.request.user
            return queryset.filter(Q(owner=user) | Q(members=user)).distinct()
        return queryset

    def perform_create(self, serializer):
        """Store the authenticated creator as the immutable board owner."""
        serializer.save(owner=self.request.user)
