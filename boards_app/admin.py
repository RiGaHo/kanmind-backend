"""Board administration."""

from django.contrib import admin

from .models import Board
from .services import set_members


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Manage board ownership and membership through the admin."""

    list_display = ["id", "title", "owner"]
    search_fields = ["title", "owner__email"]
    filter_horizontal = ["members"]

    def save_related(self, request, form, formsets, change):
        """Apply membership cleanup after admin relations have been saved."""
        super().save_related(request, form, formsets, change)
        set_members(form.instance, form.cleaned_data["members"])
