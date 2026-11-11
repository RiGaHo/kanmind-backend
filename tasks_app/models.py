"""Task and comment persistence without business logic."""

from django.conf import settings
from django.db import models


class Task(models.Model):
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
        ordering = ["id"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return self.content[:60]
