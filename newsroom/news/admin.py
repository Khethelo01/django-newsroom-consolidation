"""Admin for the News application."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    Article,
    Publisher,
    Newsletter,
    PublicationDelivery,
    ApprovalLog,
)


@admin.register(User)
class NewsUserAdmin(UserAdmin):
    """Newsuseradmin for the News application."""

    fieldsets = UserAdmin.fieldsets + (("News role", {"fields": ("role",)}),)
    list_display = ["username", "role", "email"]


for model in [
    Article,
    Publisher,
    Newsletter,
    PublicationDelivery,
    ApprovalLog,
]:
    admin.site.register(model)
