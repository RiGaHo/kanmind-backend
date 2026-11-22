"""Account data; account creation belongs to serializers/services."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class UserProfile(AbstractUser):
    """Django-compatible account with a public display name and unique email."""

    email = models.EmailField(unique=True)
    fullname = models.CharField(max_length=150)

    class Meta:
        """Order accounts by ID and enforce case-insensitive email uniqueness."""

        ordering = ["id"]
        constraints = [models.UniqueConstraint(Lower("email"), name="unique_email_ci")]

    def __str__(self):
        """Display the public name, falling back to the login identifier."""
        return self.fullname or self.username
