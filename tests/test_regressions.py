"""Account identity, admin assignment and comment ownership regressions."""

from django.core.management import call_command
from django.core.management.base import CommandError

from accounts_app.models import UserProfile
from tasks_app.forms import TaskAdminForm
from tasks_app.models import Task

from .helpers import ApiCase


class AccountIntegrityRegressionTests(ApiCase):
    def test_valid_email_does_not_become_invalid_username(self):
        long_email = "a" * 64 + "@" + "b" * 63 + "." + "c" * 63 + ".com"
        for email in ["o'brien@example.com", long_email]:
            data = {
                "fullname": "Valid Person",
                "email": email,
                "password": "Password123!",
                "repeated_password": "Password123!",
            }
            response = self.client.post("/api/registration/", data)
            self.assertEqual(response.status_code, 201)
            user = UserProfile.objects.get(pk=response.data["user_id"])
            user.full_clean()
            self.assertEqual(len(user.username), 32)

    def test_admin_form_rejects_foreign_assignee(self):
        data = self.task_payload()
        data["assignee"] = self.outsider["user_id"]
        form = TaskAdminForm(data=data, instance=Task.objects.get())
        self.assertFalse(form.is_valid())
        self.assertIn("assignee", form.errors)

    def test_guest_seed_protects_admin(self):
        UserProfile.objects.create_user(
            username="guest",
            email="guest@example.com",
            fullname="Demo Admin",
            is_staff=True,
        )
        with self.assertRaises(CommandError):
            call_command("seed_demo")

    def test_equal_names_do_not_allow_comment_deletion(self):
        UserProfile.objects.filter(pk=self.member["user_id"]).update(
            fullname=self.owner["fullname"]
        )
        comment = self.client.post(self.comments_url(), {"content": "Protected"}).data
        self.login_as(self.member)
        url = self.comments_url() + str(comment["id"]) + "/"
        self.assertEqual(self.client.delete(url).status_code, 403)
