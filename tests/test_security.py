"""Cross-cutting authentication, admin and CORS integration checks."""

from accounts_app.models import UserProfile

from .helpers import ApiCase


class SecurityTests(ApiCase):
    def protected_paths(self):
        return [
            "/api/boards/",
            self.board_url(),
            "/api/tasks/",
            self.task_url(),
            "/api/tasks/assigned-to-me/",
            "/api/tasks/reviewing/",
            "/api/email-check/?email=owner@example.com",
            self.comments_url(),
        ]

    def test_all_resource_routes_require_token(self):
        self.client.credentials()
        for path in self.protected_paths():
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.post("/api/boards/", {}).status_code, 401)
        self.assertEqual(self.client.delete(self.task_url()).status_code, 401)

    def test_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token invalid")
        self.assertEqual(self.client.get("/api/boards/").status_code, 401)

    def test_inactive_token(self):
        UserProfile.objects.filter(pk=self.owner["user_id"]).update(is_active=False)
        self.assertEqual(self.client.get("/api/boards/").status_code, 401)

    def test_cors_preflight(self):
        response = self.client.options(
            "/api/tasks/",
            HTTP_ORIGIN="http://localhost:5500",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,content-type",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["access-control-allow-origin"], "http://localhost:5500"
        )

    def test_untrusted_cors_origin(self):
        response = self.client.options(
            "/api/tasks/",
            HTTP_ORIGIN="https://untrusted.example",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )
        self.assertNotIn("access-control-allow-origin", response)

    def test_admin_login_and_model_pages(self):
        user = UserProfile.objects.get(pk=self.owner["user_id"])
        user.is_staff = user.is_superuser = True
        user.save()
        self.client.force_login(user)
        for path in [
            "/admin/",
            "/admin/accounts_app/userprofile/",
            "/admin/boards_app/board/",
            "/admin/tasks_app/task/",
            "/admin/tasks_app/comment/",
        ]:
            self.assertEqual(self.client.get(path).status_code, 200)
