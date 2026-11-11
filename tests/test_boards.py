"""Board responses, membership and ownership boundaries."""

from accounts_app.models import UserProfile
from boards_app.models import Board
from tasks_app.models import Task

from .helpers import ApiCase


class BoardTests(ApiCase):
    def test_board_summary_counts_and_detail(self):
        board = self.client.get("/api/boards/").data[0]
        self.assertEqual(board["member_count"], 2)
        self.assertEqual(board["ticket_count"], 1)
        self.assertEqual(board["tasks_to_do_count"], 1)
        self.assertEqual(board["tasks_high_prio_count"], 1)
        detail = self.client.get(self.board_url()).data
        self.assertEqual(detail["owner_id"], self.owner["user_id"])
        self.assertEqual(detail["tasks"], [self.task])
        self.assertEqual(set(detail["members"][0]), {"id", "email", "fullname"})
        self.assertEqual(self.client.get(self.board_url().rstrip("/")).status_code, 200)

    def test_members_can_update_but_cannot_delete_board(self):
        self.login_as(self.member)
        response = self.client.patch(self.board_url(), {"title": "Renamed board"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Renamed board")
        self.assertEqual(self.client.delete(self.board_url()).status_code, 403)

    def test_outsider_cannot_access_board(self):
        self.login_as(self.outsider)
        self.assertEqual(self.client.get("/api/boards/").data, [])
        self.assertEqual(self.client.get(self.board_url()).status_code, 403)
        self.assertEqual(
            self.client.patch(self.board_url(), {"title": "Bad"}).status_code, 403
        )
        self.assertEqual(self.client.delete(self.board_url()).status_code, 403)
        self.assertEqual(self.client.get("/api/boards/999999/").status_code, 404)

    def test_member_removal_clears_assignments_and_preserves_owner(self):
        response = self.client.patch(self.board_url(), {"members": []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [p["id"] for p in response.data["members"]], [self.owner["user_id"]]
        )
        self.assertIsNone(response.data["tasks"][0]["assignee"])
        self.login_as(self.member)
        self.assertEqual(self.client.get(self.board_url()).status_code, 403)
        self.assertEqual(self.client.get("/api/tasks/assigned-to-me/").data, [])

    def test_invalid_board_updates_are_atomic(self):
        for payload in [
            {"title": ""},
            {"title": "ab"},
            {"title": "x" * 64},
            {"members": [999999]},
            {"members": None},
            {"members": "bad"},
        ]:
            with self.subTest(payload=payload):
                response = self.client.patch(self.board_url(), payload)
                self.assertEqual(response.status_code, 400)
        self.assertEqual(Board.objects.get().title, "Team board")
        self.assertEqual(Board.objects.get().members.count(), 2)

    def test_delete_board_cascades_tasks_comments(self):
        self.client.post(self.comments_url(), {"content": "A comment"})
        response = self.client.delete(self.board_url())
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(Task.objects.exists())
        self.assertEqual(self.client.get(self.task_url()).status_code, 404)

    def test_membership_addition_and_owner_read_only(self):
        response = self.client.patch(
            self.board_url(),
            {
                "members": [self.outsider["user_id"]],
                "owner_id": self.outsider["user_id"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["owner_id"], self.owner["user_id"])
        self.login_as(self.outsider)
        self.assertEqual(self.client.get(self.board_url()).status_code, 200)

    def test_email_lookup(self):
        response = self.client.get("/api/email-check/", {"email": "MEMBER@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {"id", "email", "fullname"})
        self.assertEqual(response.data["id"], self.member["user_id"])
        self.assertEqual(self.client.get("/api/email-check/").status_code, 400)
        self.assertEqual(
            self.client.get("/api/email-check/?email=bad").status_code, 400
        )
        self.assertEqual(
            self.client.get("/api/email-check/?email=no@example.com").status_code, 404
        )

    def test_inactive_email_hidden(self):
        UserProfile.objects.filter(pk=self.member["user_id"]).update(is_active=False)
        self.assertEqual(
            self.client.get("/api/email-check/?email=member@example.com").status_code,
            404,
        )
