"""Account data; account creation belongs to serializers/services."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class UserProfile(AbstractUser):
    """Django-compatible account with a public display name and unique email."""

    email = models.EmailField(unique=True)
    fullname = models.CharField(max_length=150)

    class Meta:
        ordering = ["id"]
        constraints = [models.UniqueConstraint(Lower("email"), name="unique_email_ci")]

    def __str__(self):
        return self.fullname or self.username
