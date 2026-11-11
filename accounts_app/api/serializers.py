"""Account input validation and public identity representations."""

from uuid import uuid4

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts_app.models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["id", "email", "fullname"]


class RegistrationSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(write_only=True, trim_whitespace=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = UserProfile
        fields = ["fullname", "email", "password", "repeated_password"]

    def validate_email(self, value):
        value = value.lower()
        if UserProfile.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_fullname(self, value):
        if len(value.split()) < 2:
            raise serializers.ValidationError("Enter a first and last name.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("repeated_password")
        return UserProfile.objects.create_user(username=uuid4().hex, **validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)


class EmailQuerySerializer(serializers.Serializer):
    email = serializers.EmailField()
