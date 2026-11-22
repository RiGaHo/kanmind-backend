"""Account input validation and public identity representations."""

from uuid import uuid4

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts_app.models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Expose only the public account identity used in API responses."""

    class Meta:
        """Limit public user data to ID, email, and display name."""

        model = UserProfile
        fields = ["id", "email", "fullname"]


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate registration details and create password-hashed accounts."""

    repeated_password = serializers.CharField(write_only=True, trim_whitespace=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        """Accept profile details and matching password inputs."""

        model = UserProfile
        fields = ["fullname", "email", "password", "repeated_password"]

    def validate_email(self, value):
        """Normalize email casing and reject existing accounts."""
        value = value.lower()
        if UserProfile.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_fullname(self, value):
        """Require both a first and last name for public display."""
        if len(value.split()) < 2:
            raise serializers.ValidationError("Enter a first and last name.")
        return value

    def validate(self, attrs):
        """Check password confirmation and configured password rules."""
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        """Discard confirmation and create an account with an internal username."""
        validated_data.pop("repeated_password")
        return UserProfile.objects.create_user(username=uuid4().hex, **validated_data)


class LoginSerializer(serializers.Serializer):
    """Validate email and password input without trimming passwords."""

    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)


class EmailQuerySerializer(serializers.Serializer):
    """Require a valid email address for account lookup."""

    email = serializers.EmailField()
