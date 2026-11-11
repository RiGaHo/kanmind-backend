"""Task routes and comments scoped to their parent task."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CommentDetailView, CommentListView, TaskViewSet

router = DefaultRouter()
router.register("tasks", TaskViewSet)
urlpatterns = [
    path("tasks/<int:task_id>/comments/", CommentListView.as_view()),
    path("tasks/<int:task_id>/comments/<int:pk>/", CommentDetailView.as_view()),
] + router.urls
