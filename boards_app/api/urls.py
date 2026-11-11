"""Board routes including the frontend's slashless detail read."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BoardViewSet

router = DefaultRouter()
router.register("boards", BoardViewSet)
urlpatterns = [path("boards/<int:pk>", BoardViewSet.as_view({"get": "retrieve"}))]
urlpatterns += router.urls
