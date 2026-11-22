"""Task and comment administration."""

from django.contrib import admin

from .forms import TaskAdminForm
from .models import Comment, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Provide searchable task administration with workflow filters."""

    form = TaskAdminForm
    list_display = ["id", "title", "board", "status", "priority", "due_date"]
    list_filter = ["status", "priority"]
    search_fields = ["title", "description"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Provide searchable comments while protecting creation timestamps."""

    list_display = ["id", "task", "author", "created_at"]
    search_fields = ["content"]
    readonly_fields = ["created_at"]
