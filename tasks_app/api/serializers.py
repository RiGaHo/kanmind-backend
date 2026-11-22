"""Task relationship validation and frontend representations."""

from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied

from accounts_app.api.serializers import UserSerializer
from accounts_app.models import UserProfile
from boards_app.api.permissions import is_member
from boards_app.models import Board
from tasks_app.models import Comment, Task


class TaskBoardField(serializers.PrimaryKeyRelatedField):
    """Distinguish a missing board on creation from invalid request data."""

    def fail(self, key, **kwargs):
        """Translate only missing-board creation errors to the documented 404."""
        if key == "does_not_exist" and self.root.instance is None:
            raise NotFound("Board not found.")
        super().fail(key, **kwargs)


class TaskSerializer(serializers.ModelSerializer):
    """Validate task relationships and expose public participant details."""

    board = TaskBoardField(queryset=Board.objects.all())
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee",
        queryset=UserProfile.objects.filter(is_active=True),
        allow_null=True,
        required=False,
        write_only=True,
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        source="reviewer",
        queryset=UserProfile.objects.filter(is_active=True),
        allow_null=True,
        required=False,
        write_only=True,
    )
    comments_count = serializers.IntegerField(source="comments.count", read_only=True)

    class Meta:
        """Expose task attributes and separate writable participant IDs."""

        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
            "assignee_id",
            "reviewer_id",
        ]

    def validate_title(self, value):
        """Reject titles shorter than the supported minimum."""
        if len(value) < 3:
            raise serializers.ValidationError("Use at least three characters.")
        return value

    def validate(self, attrs):
        """Require board access, prevent board moves, and validate participants."""
        board = attrs.get("board", getattr(self.instance, "board", None))
        if not is_member(self.context["request"].user, board):
            raise PermissionDenied("You are not a board member.")
        if self.instance and board.pk != self.instance.board_id:
            raise serializers.ValidationError({"board": "Tasks cannot change board."})
        self.validate_people(attrs, board)
        return attrs

    def validate_people(self, attrs, board):
        """Require assigned participants to retain access to the task board."""
        for field in ["assignee", "reviewer"]:
            person = attrs.get(field, getattr(self.instance, field, None))
            if person and not is_member(person, board):
                raise serializers.ValidationError(
                    {field + "_id": "Must be a board member."}
                )


class CommentSerializer(serializers.ModelSerializer):
    """Accept comment text and expose its author name and timestamp."""

    author = serializers.CharField(source="author.fullname", read_only=True)

    class Meta:
        """Keep comment identity, authorship, and creation time read-only."""

        model = Comment
        fields = ["id", "author", "created_at", "content"]
        read_only_fields = ["id", "author", "created_at"]
