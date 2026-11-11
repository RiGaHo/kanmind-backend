"""Task relationship validation and frontend representations."""

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from accounts_app.api.serializers import UserSerializer
from accounts_app.models import UserProfile
from boards_app.api.permissions import is_member
from tasks_app.models import Comment, Task


class TaskSerializer(serializers.ModelSerializer):
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
        if len(value) < 3:
            raise serializers.ValidationError("Use at least three characters.")
        return value

    def validate(self, attrs):
        board = attrs.get("board", getattr(self.instance, "board", None))
        if not is_member(self.context["request"].user, board):
            raise PermissionDenied("You are not a board member.")
        if self.instance and board.pk != self.instance.board_id:
            raise serializers.ValidationError({"board": "Tasks cannot change board."})
        self.validate_people(attrs, board)
        return attrs

    def validate_people(self, attrs, board):
        for field in ["assignee", "reviewer"]:
            person = attrs.get(field, getattr(self.instance, field, None))
            if person and not is_member(person, board):
                raise serializers.ValidationError(
                    {field + "_id": "Must be a board member."}
                )


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.fullname", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "created_at", "content"]
        read_only_fields = ["id", "author", "created_at"]
