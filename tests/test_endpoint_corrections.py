"""Regressions for the documented board PATCH and task creation corrections."""

from boards_app.models import Board

from . import test_tasks
from .helpers import ApiCase


class EndpointCorrectionTests(ApiCase):
    """Reuse existing task fixtures and invalid payload cases for focused checks."""

    def public_user(self, account):
        """Build the documented identity independently of application serializers."""
        return {
            "id": account["user_id"],
            **{k: account[k] for k in ["email", "fullname"]},
        }

    def test_patch_identities_follow_membership_changes(self):
        """Return current public users after adding and removing board members."""
        for people in [[self.owner, self.outsider], [self.owner]]:
            payload = {
                "title": "Changed title",
                "members": [p["user_id"] for p in people],
            }
            response = self.client.patch(self.board_url(), payload)
            self.assert_patch_members(response, people)

    def assert_patch_members(self, response, people):
        """Compare the PATCH contract with expected users and stored membership."""
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Changed title")
        self.assertEqual(response.data["owner_data"], self.public_user(self.owner))
        expected = [self.public_user(p) for p in people]
        self.assertEqual(response.data["members_data"], expected)
        self.assertEqual(response.data["members"], expected)
        self.assertEqual(
            list(Board.objects.get().members.values_list("pk", flat=True)),
            [p["user_id"] for p in people],
        )

    def test_owner_deletes_after_member_patch(self):
        """A member edit and attempted owner replacement do not revoke ownership."""
        self.assertEqual(Board.objects.get().owner_id, self.owner["user_id"])
        self.login_as(self.member)
        payload = {"members": [], "owner_id": self.member["user_id"]}
        self.assertEqual(self.client.patch(self.board_url(), payload).status_code, 200)
        self.assertEqual(Board.objects.get().owner_id, self.owner["user_id"])
        self.assertEqual(self.client.delete(self.board_url()).status_code, 403)
        self.login_as(self.owner)
        self.assertEqual(self.client.delete(self.board_url()).status_code, 204)
        self.assertFalse(Board.objects.filter(pk=self.board).exists())

    def test_unknown_board_create_is_not_found(self):
        """A well-formed nonexistent board ID receives the documented 404."""
        payload = self.task_payload() | {"board": 2147483647}
        self.assertEqual(self.client.post("/api/tasks/", payload).status_code, 404)

    def test_create_authorization_statuses(self):
        """Owners and members can create tasks; outsiders still receive 403."""
        for account, status in [
            (self.owner, 201),
            (self.member, 201),
            (self.outsider, 403),
        ]:
            self.login_as(account)
            response = self.client.post("/api/tasks/", self.task_payload())
            self.assertEqual(response.status_code, status)

    def test_other_create_errors_remain_bad_requests(self):
        """Invalid task values and malformed board references remain HTTP 400."""
        cases = test_tasks.TaskTests.invalid_task_cases(self) + [
            {"board": "invalid"},
            {"board": []},
        ]
        for invalid in cases + [{"reviewer_id": self.outsider["user_id"]}]:
            with self.subTest(invalid=invalid):
                response = self.client.post(
                    "/api/tasks/", self.task_payload() | invalid
                )
                self.assertEqual(response.status_code, 400)

    def test_affected_operations_require_authentication(self):
        """Anonymous writes receive 401 before board lookup or validation."""
        self.client.credentials()
        self.assertEqual(self.client.patch(self.board_url(), {}).status_code, 401)
        payload = self.task_payload() | {"board": 2147483647}
        self.assertEqual(self.client.post("/api/tasks/", payload).status_code, 401)
