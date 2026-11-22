"""Board ownership and membership data."""

from django.conf import settings
from django.db import models


class Board(models.Model):
    """Store board ownership separately from its member collection."""

    title = models.CharField(max_length=63)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_boards"
    )
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="boards")

    class Meta:
        """Return boards in stable creation order."""

        ordering = ["id"]

    def __str__(self):
        """Identify boards by title in admin and relation widgets."""
        return self.title
