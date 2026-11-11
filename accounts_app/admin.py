"""Manage accounts with Django's password-aware admin."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Display name", {"fields": ("fullname",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Profile", {"fields": ("email", "fullname")}),
    )
    list_display = ("id", "email", "fullname", "is_staff")
