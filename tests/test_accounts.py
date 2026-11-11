"""Authentication and public account contract tests."""

from io import StringIO

from django.core.management import call_command
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile


class AccountsTests(APITestCase):
    def payload(self, **overrides):
        data = {
            "fullname": "Alice Example",
            "email": "alice@example.com",
            "password": "Password123!",
            "repeated_password": "Password123!",
        }
        return data | overrides

    def test_registration_identity_and_hashed_password(self):
        response = self.client.post("/api/registration/", self.payload())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(set(response.data), {"token", "user_id", "email", "fullname"})
        user = UserProfile.objects.get(pk=response.data["user_id"])
        self.assertTrue(user.check_password("Password123!"))
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertEqual(len(response.data["token"]), 40)

    def test_duplicate_email_is_case_insensitive(self):
        self.client.post("/api/registration/", self.payload())
        response = self.client.post(
            "/api/registration/", self.payload(email="ALICE@example.com")
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserProfile.objects.count(), 1)

    def test_invalid_registration_inputs(self):
        cases = [
            {"fullname": "Alice"},
            {"fullname": ""},
            {"email": "broken"},
            {"repeated_password": "different"},
            {"password": "short", "repeated_password": "short"},
        ]
        for data in cases:
            with self.subTest(data=data):
                response = self.client.post("/api/registration/", self.payload(**data))
                self.assertEqual(response.status_code, 400)
        self.assertEqual(UserProfile.objects.count(), 0)

    def test_login_and_inactive_account(self):
        registered = self.client.post("/api/registration/", self.payload()).data
        data = {"email": "ALICE@example.com", "password": "Password123!"}
        response = self.client.post("/api/login/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, registered)
        UserProfile.objects.update(is_active=False)
        self.assertEqual(self.client.post("/api/login/", data).status_code, 400)

    def test_invalid_login(self):
        for data in [{}, {"email": "nobody@example.com", "password": "wrong"}]:
            self.assertEqual(self.client.post("/api/login/", data).status_code, 400)

    def test_demo_account_reproducible(self):
        call_command("seed_demo", stdout=StringIO())
        call_command("seed_demo", stdout=StringIO())
        response = self.client.post(
            "/api/login/", {"email": "guest@example.com", "password": "DemoGuest2026!"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserProfile.objects.count(), 1)
        user = UserProfile.objects.get()
        self.assertFalse(user.is_staff or user.is_superuser)
