"""Secure cookie configuration in production and local HTTP development."""

import os
import runpy
from pathlib import Path
from unittest.mock import patch

from django.core.checks import run_checks
from django.http import HttpResponse
from django.test import Client, SimpleTestCase, override_settings
from django.urls import path


def session_response(request):
    request.session["example"] = True
    return HttpResponse("ok")


urlpatterns = [path("session/", session_response)]


def configuration(debug):
    env = {
        "DJANGO_DEBUG": str(debug),
        "DJANGO_SECRET_KEY": "test-only-" + "abc123" * 10,
    }
    with patch.dict(os.environ, env):
        values = runpy.run_path(
            str(Path(__file__).resolve().parents[1] / "core/settings.py")
        )
    keys = ("DEBUG", "SECRET_KEY", "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE")
    return {key: values[key] for key in keys}


class CookieConfigurationTests(SimpleTestCase):
    def test_production_cookies_are_secure(self):
        self.check_cookies(False)

    def test_local_http_cookies_remain_usable(self):
        self.check_cookies(True)

    def check_cookies(self, debug):
        values = configuration(debug)
        self.assertEqual(values["SESSION_COOKIE_SECURE"], not debug)
        self.assertEqual(values["CSRF_COOKIE_SECURE"], not debug)
        with override_settings(**values):
            response = self.client.get("/admin/login/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(bool(response.cookies["csrftoken"]["secure"]), not debug)
            self.check_session_cookie(not debug)

    @override_settings(
        ROOT_URLCONF=__name__,
        SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
    )
    def check_session_cookie(self, secure):
        response = Client().get("/session/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(bool(response.cookies["sessionid"]["secure"]), secure)

    def test_production_deploy_warnings_only_concern_upstream_https(self):
        with override_settings(**configuration(False)):
            messages = run_checks(include_deployment_checks=True)
        self.assertEqual(
            {message.id for message in messages}, {"security.W004", "security.W008"}
        )
