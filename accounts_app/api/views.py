"""Public registration/login and authenticated exact email lookup."""

from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts_app.models import UserProfile

from .serializers import (
    EmailQuerySerializer,
    LoginSerializer,
    RegistrationSerializer,
    UserSerializer,
)


def identity(user):
    """Return the authentication envelope consumed by the frontend."""
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "user_id": user.pk,
        "email": user.email,
        "fullname": user.fullname,
    }


class RegistrationView(generics.GenericAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                data = identity(serializer.save())
        except IntegrityError:
            raise ValidationError({"email": "This email is already registered."})
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        account = UserProfile.objects.filter(email__iexact=data["email"]).first()
        username = account.username if account else data["email"].lower()
        user = authenticate(username=username, password=data["password"])
        if user is None:
            raise ValidationError({"detail": "Invalid email or password."})
        return Response(identity(user))


class EmailCheckView(generics.GenericAPIView):
    serializer_class = EmailQuerySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            UserProfile,
            is_active=True,
            email__iexact=serializer.validated_data["email"],
        )
        return Response(UserSerializer(user).data)
