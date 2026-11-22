"""Task and comment persistence without business logic."""

from django.conf import settings
from django.db import models


class Task(models.Model):
    """Store a board task, its workflow state, and assigned participants."""

    STATUS = [(value, value) for value in ["to-do", "in-progress", "review", "done"]]
    PRIORITY = [(value, value) for value in ["low", "medium", "high"]]
    board = models.ForeignKey(
        "boards_app.Board", on_delete=models.CASCADE, related_name="tasks"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS, default="to-do")
    priority = models.CharField(max_length=10, choices=PRIORITY, default="medium")
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        null=True,
        blank=True,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="review_tasks",
        null=True,
        blank=True,
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_tasks",
        null=True,
    )
    due_date = models.DateField()

    class Meta:
        """Return tasks in stable creation order."""

        ordering = ["id"]

    def __str__(self):
        """Identify tasks by title in admin and relation widgets."""
        return self.title


class Comment(models.Model):
    """Store an authored, timestamped message belonging to a task."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Order comments chronologically with a stable tie breaker."""

        ordering = ["created_at", "id"]

    def __str__(self):
        """Show a short content preview in admin relation widgets."""
        return self.content[:60]
