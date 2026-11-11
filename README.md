# KanMind API

Standalone Django / Django REST Framework backend for KanMind. Python 3.12+
(required by Django 6), pip and SQLite support are required. No frontend, Node,
external database, or account credentials are required to run the backend/tests.

## Install and start

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

The API is at `http://127.0.0.1:8000/api/`. Create an administrator with
`python manage.py createsuperuser`, then visit `/admin/`. The standard admin
supports accounts, boards, tasks and comments. API accounts have no admin rights.
Migrations are committed; the local SQLite database is ignored.

`seed_demo` creates (or resets) `guest@example.com` / `DemoGuest2026!` with the
name **Demo Guest**. These are intentionally public demonstration credentials.
The command refuses to reset a privileged account. It does not create boards or
tasks: create them through the API. Do not use this account on a public service.

## Configuration

Environment variables are read directly; `.env` files are not automatically loaded.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_DEBUG` | `true` | Local development mode; use `false` in deployment |
| `DJANGO_SECRET_KEY` | Public development-only value | Required override when debug is false |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` | Comma-separated host names |
| `DJANGO_DB_PATH` | `db.sqlite3` in project root | SQLite location |
| `CORS_ALLOWED_ORIGINS` | localhost and 127.0.0.1 on ports 5500 and 3000 | Comma-separated browser origins |

Use HTTPS, an appropriate WSGI/ASGI server, secure cookie/proxy settings and
`python manage.py check --deploy` for an actual deployment. `runserver` and the
provided defaults are for local review. API authentication uses tokens; the admin
uses Django sessions and CSRF protection. API tokens persist until deleted from
the database/admin; frontend logout removes the browser copy only.

## API contract

Send JSON and `Authorization: Token <token>`. Registration and login are public;
all resource endpoints require an active user. Lists are plain JSON arrays.

| Path under `/api/` | Methods | Request |
| --- | --- | --- |
| `registration/` | POST | fullname, email, password, repeated_password |
| `login/` | POST | email, password |
| `email-check/` | GET | `?email=<URL-encoded email>` |
| `boards/` | GET, POST | title, members (array of user IDs, optional) |
| `boards/{id}/` | GET, PUT, PATCH, DELETE | title and/or members |
| `tasks/` | GET, POST | board, title, due_date; optional description, status, priority, assignee_id, reviewer_id |
| `tasks/{id}/` | GET, PUT, PATCH, DELETE | Task fields |
| `tasks/assigned-to-me/` | GET | None |
| `tasks/reviewing/` | GET | None |
| `tasks/{id}/comments/` | GET, POST | content |
| `tasks/{id}/comments/{comment_id}/` | DELETE | None |

Registration (201) and login (200) return `token`, `user_id`, `email`, `fullname`.
Email lookup returns `{id,email,fullname}` or 404. Email matching is case
insensitive; names require at least two parts for frontend initials; passwords
require at least eight characters. Internal usernames are independent of email.

Board lists include `id,title,owner_id,members,member_count,ticket_count,
tasks_to_do_count,tasks_high_prio_count`; list/create members are IDs. Detail and
update responses expand members into user objects and add nested `tasks`.
Slashless board detail GET is supported for the supplied frontend.

Tasks return `id,board,title,description,status,priority,assignee,reviewer,due_date,
comments_count`. Assignee/reviewer are user objects or null; write their IDs with
`assignee_id`/`reviewer_id`, including null to unassign. Status is `to-do`,
`in-progress`, `review` or `done`; priority is `low`, `medium` or `high`.
Dates use `YYYY-MM-DD`; past deadlines are allowed. Board titles require 3–63
characters and task titles 3–255 characters. Task board changes are rejected.

Comments return `id,author,created_at,content`; author is a display-name string,
and created_at is a UTC ISO timestamp. Author identity always comes from the token.
Successful create returns 201, read/update 200, and delete 204 with no body.
Validation errors are field-keyed JSON (400); invalid/missing tokens return 401,
forbidden object access 403, missing resources 404. Unsupported methods return 405.

### Authorization decisions

The supplied frontend does not specify every permission edge case. These explicit
policies apply consistently: owners are always board members; members can update
boards, membership and tasks; only owners delete boards. Task creators or board
owners may delete tasks. Only comment authors may delete their comments, even
when another user has the same name. Nested comment IDs are scoped to their task.
Nonmembers cannot access existing board/task/comment objects. Personal lists only
include accessible tasks. Removing members clears their assignments and review
roles. Admin board/task forms preserve these membership invariants too.

### Example

```sh
curl -sS http://127.0.0.1:8000/api/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"guest@example.com","password":"DemoGuest2026!"}'
# Use the returned token:
curl -sS http://127.0.0.1:8000/api/boards/ \
  -H 'Authorization: Token YOUR_TOKEN'
```

## Verification

```sh
python manage.py test tests
# Faster isolated test hashing (never use these settings to serve the app):
python manage.py test tests --settings=tests.settings
python manage.py check
python manage.py makemigrations --check --dry-run
ruff check .
ruff format --check .
python tools/check_conventions.py
python tools/http_smoke.py
```

The HTTP smoke test creates a temporary database, migrates it, starts a real local
server on an available port, exercises the API, and stops the server. It needs no
running server or frontend. Tests cover authentication, response contracts,
permissions, membership, assignments, validation, nested comments, admin and CORS.
The external PM tests are unavailable: local passing tests or code coverage cannot
prove their required 95% pass rate.

## Project structure and limitations

`core` holds settings and routing; `accounts_app`, `boards_app`, and `tasks_app`
each expose an `api/` package. CRUD uses explicit-field ModelSerializers and DRF
viewsets/generics. Membership operations live in services, not model methods.
Tests and verification tools are part of this backend repository.

A local `frontend/` copy may be present for configuration/reference only and is
fully ignored by Git. Backend commands do not read it. Original frontend logic
remains unchanged. Known reference frontend issues: create-dialog member removal
uses an ID as an array offset; membership updates can render before completion;
plus-address lookup is not URL-encoded; templates insert text using innerHTML.
Use fictional demo data. These frontend issues are documented, not silently fixed
by changing API content or frontend application logic.

No databases, virtual environments, real secrets, or outer working logs belong in
this repository. The separate review archive includes the original inputs and
local frontend copy, while excluding environments, databases, caches and secrets.
