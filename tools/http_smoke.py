"""Real HTTP contract checks using an isolated database and local server."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def request(base, path, method="GET", data=None, token=None, expected=200):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Token " + token
    body = json.dumps(data).encode() if data is not None else None
    req = Request(base + path, data=body, headers=headers, method=method)
    try:
        response = urlopen(req, timeout=5)
    except HTTPError as error:
        response = error
    with response:
        assert response.status == expected, (path, response.status, response.read())
        content = response.read()
    return json.loads(content) if content else None


def available_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(base, process):
    for _ in range(100):
        assert process.poll() is None, "Server exited before accepting requests"
        try:
            request(base, "boards/", expected=401)
            return
        except (URLError, ConnectionError):
            time.sleep(0.1)
    raise AssertionError("Server did not start")


def create_account(base, name):
    return request(
        base,
        "registration/",
        "POST",
        {
            "fullname": name.title() + " Example",
            "email": name + "@example.com",
            "password": "SmokePassword42!",
            "repeated_password": "SmokePassword42!",
        },
        expected=201,
    )


def create_board_task(base, owner, member):
    data = {"title": "HTTP board", "members": [member["user_id"]]}
    board = request(base, "boards/", "POST", data, owner["token"], 201)
    data = {
        "board": board["id"],
        "title": "HTTP task",
        "due_date": "2027-01-01",
        "assignee_id": member["user_id"],
        "reviewer_id": owner["user_id"],
    }
    task = request(base, "tasks/", "POST", data, owner["token"], 201)
    return board, task


def check_comments(base, token, task):
    path = f"tasks/{task['id']}/comments/"
    comment = request(base, path, "POST", {"content": "HTTP comment"}, token, 201)
    assert request(base, path, token=token) == [comment]
    request(base, path, "POST", {"content": " "}, token, 400)
    request(base, path + str(comment["id"]) + "/", "DELETE", token=token, expected=204)


def check_permissions(base, board, task, outsider):
    token = outsider["token"]
    assert request(base, "boards/", token=token) == []
    request(base, f"boards/{board['id']}/", token=token, expected=403)
    request(base, f"tasks/{task['id']}/", "PATCH", {"status": "done"}, token, 403)
    request(base, f"tasks/{task['id']}/comments/", token=token, expected=403)
    request(base, "tasks/999999/", token=token, expected=404)


def check_task(base, task, owner, member):
    path = f"tasks/{task['id']}/"
    assert request(base, "tasks/assigned-to-me/", token=member["token"]) == [task]
    assert request(base, "tasks/reviewing/", token=owner["token"]) == [task]
    changed = request(base, path, "PATCH", {"status": "done"}, member["token"])
    assert changed["status"] == "done"
    request(base, path, "PATCH", {"priority": "invalid"}, owner["token"], 400)
    request(base, path, "DELETE", token=member["token"], expected=403)


def check_identity(base, owner, member):
    data = {"email": owner["email"], "password": "SmokePassword42!"}
    assert request(base, "login/", "POST", data) == owner
    path = "email-check/?email=member%40example.com"
    assert request(base, path, token=owner["token"])["id"] == member["user_id"]


def check_board_and_delete(base, board, task, token):
    path = f"boards/{board['id']}"
    assert request(base, path, token=token)["tasks"][0]["id"] == task["id"]
    request(base, f"tasks/{task['id']}/", "DELETE", token=token, expected=204)
    request(base, path + "/", "DELETE", token=token, expected=204)


def exercise(base):
    names = ["owner", "member", "outsider"]
    owner, member, outsider = [create_account(base, name) for name in names]
    check_identity(base, owner, member)
    board, task = create_board_task(base, owner, member)
    check_task(base, task, owner, member)
    check_comments(base, owner["token"], task)
    check_permissions(base, board, task, outsider)
    check_board_and_delete(base, board, task, owner["token"])


def migrate_database(env):
    command = [sys.executable, "manage.py", "migrate", "--noinput"]
    subprocess.run(command, cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)


def serve_and_test(port, env, log):
    command = [sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}"]
    process = subprocess.Popen(
        command + ["--noreload"], cwd=ROOT, env=env, stdout=log, stderr=log
    )
    try:
        base = f"http://127.0.0.1:{port}/api/"
        wait_for_server(base, process)
        exercise(base)
    finally:
        process.terminate()
        process.wait(timeout=10)


def run_server(folder):
    env = dict(os.environ, DJANGO_DB_PATH=str(Path(folder) / "http.sqlite3"))
    env["DJANGO_SETTINGS_MODULE"] = "core.settings"
    migrate_database(env)
    with open(Path(folder) / "server.log", "w") as log:
        serve_and_test(available_port(), env, log)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="kanmind-http-") as temporary:
        run_server(temporary)
    sys.stdout.write("Real HTTP smoke checks passed.\n")
