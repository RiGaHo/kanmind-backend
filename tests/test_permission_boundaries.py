"""Deletion roles, revoked access and immutable resource ownership."""

from boards_app.models import Board
from tasks_app.models import Comment, Task

from .helpers import ApiCase


class PermissionBoundaryTests(ApiCase):
    def test_owner_can_delete_member_created_task(self):
        self.login_as(self.member)
        task = self.create_task()
        self.login_as(self.owner)
        response = self.client.delete(f"/api/tasks/{task['id']}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Task.objects.filter(pk=task["id"]).exists())

    def test_reviewer_role_does_not_grant_delete(self):
        self.client.patch(self.task_url(), {"reviewer_id": self.member["user_id"]})
        self.login_as(self.member)
        response = self.client.delete(self.task_url())
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Task.objects.filter(pk=self.task["id"]).exists())

    def test_removed_creator_cannot_delete_own_task(self):
        self.login_as(self.member)
        task = self.create_task()
        self.login_as(self.owner)
        self.assertEqual(
            self.client.patch(self.board_url(), {"members": []}).status_code, 200
        )
        self.login_as(self.member)
        self.assertEqual(
            self.client.delete(f"/api/tasks/{task['id']}/").status_code, 403
        )
        self.assertTrue(Task.objects.filter(pk=task["id"]).exists())

    def test_owner_can_delete_task_after_creator_leaves(self):
        self.login_as(self.member)
        task = self.create_task()
        self.login_as(self.owner)
        self.client.patch(self.board_url(), {"members": []})
        self.assertEqual(
            self.client.delete(f"/api/tasks/{task['id']}/").status_code, 204
        )

    def test_task_creator_cannot_be_spoofed_on_create(self):
        self.login_as(self.member)
        task = self.create_task(
            creator=self.outsider["user_id"], creator_id=self.outsider["user_id"]
        )
        self.assertEqual(
            Task.objects.get(pk=task["id"]).creator_id, self.member["user_id"]
        )
        self.assertEqual(
            self.client.delete(f"/api/tasks/{task['id']}/").status_code, 204
        )

    def test_task_creator_cannot_be_claimed_by_patch(self):
        self.login_as(self.member)
        payload = {
            "creator": self.member["user_id"],
            "creator_id": self.member["user_id"],
        }
        self.assertEqual(self.client.patch(self.task_url(), payload).status_code, 200)
        self.assertEqual(
            Task.objects.get(pk=self.task["id"]).creator_id, self.owner["user_id"]
        )
        self.assertEqual(self.client.delete(self.task_url()).status_code, 403)

    def test_member_cannot_claim_board_ownership(self):
        self.login_as(self.member)
        payload = {"owner": self.member["user_id"], "owner_id": self.member["user_id"]}
        self.assertEqual(self.client.patch(self.board_url(), payload).status_code, 200)
        self.assertEqual(
            Board.objects.get(pk=self.board).owner_id, self.owner["user_id"]
        )
        self.assertEqual(self.client.delete(self.board_url()).status_code, 403)

    def test_denied_board_delete_preserves_nested_resources(self):
        comment = self.client.post(self.comments_url(), {"content": "Keep me"}).data
        self.login_as(self.member)
        self.assertEqual(self.client.delete(self.board_url()).status_code, 403)
        self.assertTrue(Board.objects.filter(pk=self.board).exists())
        self.assertTrue(Task.objects.filter(pk=self.task["id"]).exists())
        self.assertTrue(Comment.objects.filter(pk=comment["id"]).exists())

    def test_anonymous_delete_requires_authentication(self):
        comment = self.client.post(self.comments_url(), {"content": "Private"}).data
        paths = [
            self.board_url(),
            self.task_url(),
            self.comments_url() + str(comment["id"]) + "/",
        ]
        self.client.credentials()
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.delete(path).status_code, 401)
        self.assertTrue(Comment.objects.filter(pk=comment["id"]).exists())

    def test_removed_author_cannot_delete_comment(self):
        self.login_as(self.member)
        comment = self.client.post(self.comments_url(), {"content": "Retained"}).data
        self.login_as(self.owner)
        self.client.patch(self.board_url(), {"members": []})
        self.login_as(self.member)
        path = self.comments_url() + str(comment["id"]) + "/"
        self.assertEqual(self.client.delete(path).status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=comment["id"]).exists())

    def test_malformed_json_does_not_modify_task(self):
        response = self.client.patch(
            self.task_url(), '{"status":', content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.get(pk=self.task["id"]).status, "to-do")
