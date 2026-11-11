"""Nested comments must obey both author and parent boundaries."""

from .helpers import ApiCase


class CommentTests(ApiCase):
    def test_comment_creation_and_count(self):
        response = self.client.post(self.comments_url(), {"content": "Hello team"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(set(response.data), {"id", "author", "created_at", "content"})
        self.assertEqual(response.data["author"], self.owner["fullname"])
        self.assertIn("T", response.data["created_at"])
        self.assertEqual(self.client.get(self.comments_url()).data, [response.data])
        self.assertEqual(self.client.get(self.task_url()).data["comments_count"], 1)

    def test_only_author_can_delete(self):
        self.login_as(self.member)
        comment = self.client.post(self.comments_url(), {"content": "By member"}).data
        url = self.comments_url() + str(comment["id"]) + "/"
        self.login_as(self.owner)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.login_as(self.member)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.delete(url).status_code, 404)

    def test_comment_parent_mismatch(self):
        comment = self.client.post(self.comments_url(), {"content": "Original"}).data
        other = self.create_task()
        url = f"/api/tasks/{other['id']}/comments/{comment['id']}/"
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(len(self.client.get(self.comments_url()).data), 1)

    def test_outsider_and_missing_parent(self):
        comment = self.client.post(self.comments_url(), {"content": "Private"}).data
        self.login_as(self.outsider)
        self.assertEqual(self.client.get(self.comments_url()).status_code, 403)
        self.assertEqual(
            self.client.post(self.comments_url(), {"content": "Bad"}).status_code, 403
        )
        url = self.comments_url() + str(comment["id"]) + "/"
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.assertEqual(self.client.get("/api/tasks/99999/comments/").status_code, 404)

    def test_blank_comments_and_author_spoof(self):
        for data in [{}, {"content": ""}, {"content": "   "}, {"content": None}]:
            self.assertEqual(
                self.client.post(self.comments_url(), data).status_code, 400
            )
        response = self.client.post(
            self.comments_url(),
            {"content": "Actual author", "author": self.outsider["fullname"]},
        )
        self.assertEqual(response.data["author"], self.owner["fullname"])
