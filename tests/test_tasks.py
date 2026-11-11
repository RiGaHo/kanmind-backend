"""Task contract, permissions, assignment and validation tests."""

from tasks_app.models import Task

from .helpers import ApiCase


class TaskTests(ApiCase):
    def test_response_and_dashboard_lists(self):
        self.assertEqual(self.task["assignee"]["id"], self.member["user_id"])
        self.assertEqual(self.task["reviewer"]["id"], self.owner["user_id"])
        self.assertEqual(self.task["comments_count"], 0)
        self.assertEqual(self.client.get("/api/tasks/reviewing/").data, [self.task])
        self.assertEqual(self.client.get("/api/tasks/assigned-to-me/").data, [])
        self.login_as(self.member)
        self.assertEqual(
            self.client.get("/api/tasks/assigned-to-me/").data, [self.task]
        )
        self.assertEqual(self.client.get("/api/tasks/reviewing/").data, [])

    def test_status_transitions_and_null_assignments(self):
        self.login_as(self.member)
        for status in ["in-progress", "review", "done", "to-do"]:
            response = self.client.patch(self.task_url(), {"status": status})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["status"], status)
        response = self.client.patch(
            self.task_url(), {"assignee_id": None, "reviewer_id": None}
        )
        self.assertIsNone(response.data["assignee"])
        self.assertIsNone(response.data["reviewer"])

    def invalid_task_cases(self):
        return [
            {"title": "ab"},
            {"title": ""},
            {"status": "unknown"},
            {"priority": "urgent"},
            {"due_date": "2027-02-30"},
            {"due_date": None},
            {"board": None},
            {"assignee_id": 99999},
            {"reviewer_id": "invalid"},
            {"assignee_id": self.outsider["user_id"]},
        ]

    def test_invalid_task_fields(self):
        for payload in self.invalid_task_cases():
            with self.subTest(payload=payload):
                self.assertEqual(
                    self.client.patch(self.task_url(), payload).status_code, 400
                )
        self.assertEqual(Task.objects.get().status, "to-do")

    def test_missing_create_fields(self):
        for data in [{}, {"board": self.board}, {"board": self.board, "title": "Test"}]:
            self.assertEqual(self.client.post("/api/tasks/", data).status_code, 400)
        self.assertEqual(Task.objects.count(), 1)

    def test_outsider_all_task_operations(self):
        self.login_as(self.outsider)
        self.assertEqual(self.client.get("/api/tasks/").data, [])
        self.assertEqual(self.client.get(self.task_url()).status_code, 403)
        self.assertEqual(
            self.client.patch(self.task_url(), {"status": "done"}).status_code, 403
        )
        self.assertEqual(self.client.delete(self.task_url()).status_code, 403)
        data = {"board": self.board, "title": "Unauthorized", "due_date": "2027-01-01"}
        self.assertEqual(self.client.post("/api/tasks/", data).status_code, 403)

    def test_task_deletion_creator_or_board_owner(self):
        self.login_as(self.member)
        self.assertEqual(self.client.delete(self.task_url()).status_code, 403)
        own = self.create_task()
        self.assertEqual(
            self.client.delete(f"/api/tasks/{own['id']}/").status_code, 204
        )
        self.login_as(self.owner)
        self.assertEqual(self.client.delete(self.task_url()).status_code, 204)

    def test_cannot_move_tasks_between_boards(self):
        board = self.client.post("/api/boards/", {"title": "Other board"}).data["id"]
        response = self.client.patch(self.task_url(), {"board": board})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.get().board_id, self.board)

    def test_missing_resources(self):
        for method in [self.client.get, self.client.patch, self.client.delete]:
            self.assertEqual(method("/api/tasks/999999/").status_code, 404)

    def test_full_update(self):
        data = {
            "board": self.board,
            "title": "Full replacement",
            "description": "New",
            "status": "done",
            "priority": "low",
            "due_date": "2027-02-02",
        }
        response = self.client.put(self.task_url(), data)
        self.assertEqual(response.status_code, 200)
        for field, value in data.items():
            self.assertEqual(response.data[field], value)
