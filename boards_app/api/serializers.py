"""Board write payloads and summary/detail responses."""

from django.db import transaction
from rest_framework import serializers

from accounts_app.api.serializers import UserSerializer
from accounts_app.models import UserProfile
from boards_app.models import Board
from boards_app.services import set_members
from tasks_app.api.serializers import TaskSerializer


class BoardSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=UserProfile.objects.filter(is_active=True), required=False
    )
    member_count = serializers.IntegerField(source="members.count", read_only=True)
    ticket_count = serializers.IntegerField(source="tasks.count", read_only=True)
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "members",
            "owner_id",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
        ]
        read_only_fields = ["owner_id"]

    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Use at least three characters.")
        return value

    def get_tasks_to_do_count(self, obj):
        return sum(task.status == "to-do" for task in obj.tasks.all())

    def get_tasks_high_prio_count(self, obj):
        return sum(task.priority == "high" for task in obj.tasks.all())

    @transaction.atomic
    def create(self, validated_data):
        members = validated_data.pop("members", [])
        board = Board.objects.create(**validated_data)
        set_members(board, members)
        return board

    @transaction.atomic
    def update(self, instance, validated_data):
        members = validated_data.pop("members", None)
        instance = super().update(instance, validated_data)
        if members is not None:
            set_members(instance, members)
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context["view"].action in ["retrieve", "update", "partial_update"]:
            data["members"] = UserSerializer(instance.members.all(), many=True).data
            data["tasks"] = TaskSerializer(instance.tasks.all(), many=True).data
        return data
