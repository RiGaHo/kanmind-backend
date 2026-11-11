"""Fast hashing only for the isolated automated test process."""

from core.settings import *  # noqa: F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
