"""Admin validation preserves the same task invariants as the API."""

from django import forms

from boards_app.api.permissions import is_member

from .models import Task


class TaskAdminForm(forms.ModelForm):
    """Apply board and assignment constraints to admin task edits."""

    class Meta:
        """Expose editable task attributes in the admin form."""

        model = Task
        fields = [
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "creator",
            "due_date",
        ]

    def clean(self):
        """Reject board moves and assignments outside the selected board."""
        data = super().clean()
        board = data.get("board")
        if board:
            self.validate_members(data, board)
        if self.instance.pk and board and board.pk != self.instance.board_id:
            self.add_error("board", "Tasks cannot change board.")
        return data

    def validate_members(self, data, board):
        """Attach field errors for assignees or reviewers without board access."""
        for field in ["assignee", "reviewer"]:
            user = data.get(field)
            if user and not is_member(user, board):
                self.add_error(field, "Must be a board member.")
