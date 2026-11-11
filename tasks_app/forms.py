"""Admin validation preserves the same task invariants as the API."""

from django import forms

from boards_app.api.permissions import is_member

from .models import Task


class TaskAdminForm(forms.ModelForm):
    class Meta:
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
        data = super().clean()
        board = data.get("board")
        if board:
            self.validate_members(data, board)
        if self.instance.pk and board and board.pk != self.instance.board_id:
            self.add_error("board", "Tasks cannot change board.")
        return data

    def validate_members(self, data, board):
        for field in ["assignee", "reviewer"]:
            user = data.get(field)
            if user and not is_member(user, board):
                self.add_error(field, "Must be a board member.")
