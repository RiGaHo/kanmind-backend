"""Shared API fixtures, created through the public contract."""

from rest_framework.test import APITestCase


class ApiCase(APITestCase):
    def setUp(self):
        self.owner = self.register("owner")
        self.member = self.register("member")
        self.outsider = self.register("outsider")
        self.login_as(self.owner)
        response = self.client.post(
            "/api/boards/", {"title": "Team board", "members": [self.member["user_id"]]}
        )
        self.assertEqual(response.status_code, 201)
        self.board = response.data["id"]
        self.task = self.create_task()

    def register(self, name):
        response = self.client.post(
            "/api/registration/",
            {
                "fullname": name.title() + " Example",
                "email": name + "@example.com",
                "password": "TestPassword42!",
                "repeated_password": "TestPassword42!",
            },
        )
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def login_as(self, account):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + account["token"])

    def task_payload(self):
        return {
            "board": self.board,
            "title": "Example task",
            "description": "Text",
            "status": "to-do",
            "priority": "high",
            "due_date": "2027-01-20",
            "assignee_id": self.member["user_id"],
            "reviewer_id": self.owner["user_id"],
        }

    def create_task(self, **overrides):
        response = self.client.post("/api/tasks/", self.task_payload() | overrides)
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def task_url(self):
        return f"/api/tasks/{self.task['id']}/"

    def board_url(self):
        return f"/api/boards/{self.board}/"

    def comments_url(self):
        return self.task_url() + "comments/"
